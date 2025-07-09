#!/usr/bin/env python3
"""
Multi-Agent System for Smart File Management
Based on MAFM architecture with Ollama integration
"""
import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging
import aiohttp
from pathlib import Path

logger = logging.getLogger(__name__)

class AgentRole(Enum):
    SUPERVISOR = "supervisor"
    MEMBER = "member"
    ANALYST = "analyst"

@dataclass
class Agent:
    name: str
    role: AgentRole
    directory: Optional[str] = None
    model: str = "llama3.2:3b"

class MultiAgentSystem:
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.agents = self._initialize_agents()
        
    def _initialize_agents(self) -> Dict[str, Agent]:
        """Initialize all agents in the system"""
        agents = {}
        
        # Supervisor agent - decides which directories to search
        agents["supervisor"] = Agent(
            name="Supervisor",
            role=AgentRole.SUPERVISOR,
            model="llama3.2:3b"
        )
        
        # Directory-specific agents
        directories = {
            "documents": os.path.expanduser("~/Documents"),
            "downloads": os.path.expanduser("~/Downloads"),
            "desktop": os.path.expanduser("~/Desktop"),
            "pictures": os.path.expanduser("~/Pictures"),
            "projects": os.path.expanduser("~/Projects") if os.path.exists(os.path.expanduser("~/Projects")) else None
        }
        
        for name, path in directories.items():
            if path and os.path.exists(path):
                agents[f"member_{name}"] = Agent(
                    name=f"{name.capitalize()} Agent",
                    role=AgentRole.MEMBER,
                    directory=path,
                    model="llama3.2:3b"
                )
                
        # Analyst agent - consolidates and filters results
        agents["analyst"] = Agent(
            name="Analyst",
            role=AgentRole.ANALYST,
            model="llama3.2:3b"
        )
        
        return agents
        
    async def process_query(self, query: str) -> Dict[str, Any]:
        """Process user query through multi-agent system"""
        logger.info(f"Processing query: {query}")
        
        # Step 1: Supervisor determines relevant directories
        relevant_dirs = await self._supervisor_analyze(query)
        logger.info(f"Supervisor selected directories: {relevant_dirs}")
        
        # Step 2: Member agents search their directories
        search_tasks = []
        for dir_name in relevant_dirs:
            agent_name = f"member_{dir_name.lower()}"
            if agent_name in self.agents:
                task = self._member_search(
                    self.agents[agent_name],
                    query
                )
                search_tasks.append(task)
                
        # Execute searches in parallel
        search_results = await asyncio.gather(*search_tasks)
        
        # Step 3: Analyst consolidates results
        final_results = await self._analyst_consolidate(query, search_results)
        
        return {
            "query": query,
            "searched_directories": relevant_dirs,
            "results": final_results,
            "agent_count": len(search_tasks) + 2  # members + supervisor + analyst
        }
        
    async def _supervisor_analyze(self, query: str) -> List[str]:
        """Supervisor agent analyzes query and selects directories"""
        prompt = f"""As a file system supervisor, analyze this search query and determine which directories are most likely to contain relevant files.

Available directories:
- Documents: General documents, reports, text files
- Downloads: Downloaded files from internet
- Desktop: Files on desktop
- Pictures: Images and photos
- Projects: Code and project files

Query: "{query}"

Based on the query, select the most relevant directories to search.
Respond with a JSON array of directory names.

Example: ["documents", "downloads"]"""

        try:
            response = await self._call_ollama(prompt, json_format=True)
            directories = json.loads(response)
            
            # Validate directories
            valid_dirs = []
            for d in directories:
                if isinstance(d, str) and f"member_{d.lower()}" in self.agents:
                    valid_dirs.append(d.lower())
                    
            # If no valid directories, search all
            if not valid_dirs:
                valid_dirs = ["documents", "downloads", "desktop"]
                
            return valid_dirs
            
        except Exception as e:
            logger.error(f"Supervisor error: {e}")
            # Fallback to searching common directories
            return ["documents", "downloads", "desktop"]
            
    async def _member_search(self, agent: Agent, query: str) -> Dict[str, Any]:
        """Member agent searches its directory"""
        logger.info(f"{agent.name} searching in {agent.directory}")
        
        # Get file list from directory
        files = []
        try:
            for root, _, filenames in os.walk(agent.directory):
                for filename in filenames[:100]:  # Limit for performance
                    if not filename.startswith('.'):
                        file_path = os.path.join(root, filename)
                        files.append({
                            "path": file_path,
                            "name": filename,
                            "size": os.path.getsize(file_path)
                        })
        except Exception as e:
            logger.error(f"Error scanning directory: {e}")
            
        if not files:
            return {
                "agent": agent.name,
                "directory": agent.directory,
                "files": []
            }
            
        # Use LLM to filter relevant files
        file_list = "\n".join([f"{i+1}. {f['name']}" for i, f in enumerate(files[:50])])
        
        prompt = f"""You are a file search agent for the {agent.name} directory.
Analyze these files and select which ones are most relevant to the search query.

Query: "{query}"

Files in directory:
{file_list}

Select the most relevant files (by number) and explain why they match.
Respond in JSON format:
{{"relevant_files": [1, 3, 5], "reasoning": "..."}}"""

        try:
            response = await self._call_ollama(prompt, json_format=True)
            result = json.loads(response)
            
            # Extract selected files
            selected_files = []
            for idx in result.get("relevant_files", []):
                if isinstance(idx, int) and 0 < idx <= len(files):
                    selected_files.append(files[idx - 1])
                    
            return {
                "agent": agent.name,
                "directory": agent.directory,
                "files": selected_files,
                "reasoning": result.get("reasoning", "")
            }
            
        except Exception as e:
            logger.error(f"Member search error: {e}")
            # Fallback to simple keyword matching
            keyword_files = []
            query_lower = query.lower()
            for f in files[:20]:
                if query_lower in f['name'].lower():
                    keyword_files.append(f)
                    
            return {
                "agent": agent.name,
                "directory": agent.directory,
                "files": keyword_files
            }
            
    async def _analyst_consolidate(self, query: str, 
                                 search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyst agent consolidates and ranks results"""
        # Collect all files from all agents
        all_files = []
        for result in search_results:
            for file in result.get("files", []):
                file["source_agent"] = result["agent"]
                all_files.append(file)
                
        if not all_files:
            return []
            
        # Use LLM to rank and filter final results
        file_list = "\n".join([
            f"{i+1}. {f['name']} (from {f['source_agent']})"
            for i, f in enumerate(all_files)
        ])
        
        prompt = f"""As an analyst agent, review all search results and provide the final ranked list of most relevant files.

Original query: "{query}"

All found files:
{file_list}

Analyze these files and:
1. Rank them by relevance to the query
2. Remove any clearly irrelevant results
3. Provide a brief reason for the top results

Respond in JSON format:
{{"ranked_files": [1, 3, 2], "reasons": {{"1": "...", "3": "..."}}}}"""

        try:
            response = await self._call_ollama(prompt, json_format=True)
            result = json.loads(response)
            
            # Build final results
            final_files = []
            for idx in result.get("ranked_files", [])[:10]:  # Top 10 results
                if isinstance(idx, int) and 0 < idx <= len(all_files):
                    file = all_files[idx - 1].copy()
                    file["relevance_reason"] = result.get("reasons", {}).get(str(idx), "")
                    file["rank"] = len(final_files) + 1
                    final_files.append(file)
                    
            return final_files
            
        except Exception as e:
            logger.error(f"Analyst error: {e}")
            # Return all files as fallback
            return all_files[:10]
            
    async def _call_ollama(self, prompt: str, json_format: bool = False) -> str:
        """Call Ollama API"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": "llama3.2:3b",
                    "prompt": prompt,
                    "stream": False
                }
                
                if json_format:
                    payload["format"] = "json"
                    
                async with session.post(
                    f"{self.ollama_url}/api/generate",
                    json=payload
                ) as resp:
                    result = await resp.json()
                    return result.get("response", "{}")
                    
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            return "{}" if json_format else ""
            
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        status = {
            "total_agents": len(self.agents),
            "agents": {}
        }
        
        for name, agent in self.agents.items():
            status["agents"][name] = {
                "name": agent.name,
                "role": agent.role.value,
                "directory": agent.directory,
                "model": agent.model,
                "active": True
            }
            
        return status