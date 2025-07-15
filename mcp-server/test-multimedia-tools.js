#!/usr/bin/env node

// Test script to verify multimedia tools are properly registered
import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

// Read the built index.js to check if tools are registered
const indexPath = join(__dirname, 'dist', 'index.js');
const indexContent = readFileSync(indexPath, 'utf-8');

// List of multimedia tools to check
const multimediaTools = [
  'analyze_media_vision',
  'transcribe_media', 
  'search_multimedia',
  'generate_media_preview',
  'organize_media_smart',
  'extract_media_content',
  'monitor_media_changes'
];

console.log('🔍 Checking MCP Server v4.0 Multimedia Tools Integration...\n');

// Check if each tool is registered
let allFound = true;
multimediaTools.forEach(tool => {
  const toolRegistered = indexContent.includes(`name: "${tool}"`);
  const handlerExists = indexContent.includes(`case "${tool}":`);
  
  if (toolRegistered && handlerExists) {
    console.log(`✅ ${tool} - Registered and handler exists`);
  } else if (toolRegistered) {
    console.log(`⚠️  ${tool} - Registered but handler missing`);
    allFound = false;
  } else {
    console.log(`❌ ${tool} - Not registered`);
    allFound = false;
  }
});

// Check for multimedia imports
console.log('\n📦 Checking multimedia imports...');
const hasSchemaImport = indexContent.includes('schemas/multimedia.js');
const hasHandlerImport = indexContent.includes('handlers/multimedia.js');

if (hasSchemaImport && hasHandlerImport) {
  console.log('✅ Multimedia schemas and handlers imported');
} else {
  console.log('❌ Missing multimedia imports');
  allFound = false;
}

// Summary
console.log('\n📊 Summary:');
if (allFound) {
  console.log('✅ All 7 multimedia tools are properly integrated!');
  console.log('🚀 MCP Server v4.0 is ready for multimedia processing');
} else {
  console.log('❌ Some multimedia tools are missing or incomplete');
  console.log('Please check the implementation');
}

console.log('\n💡 Next steps:');
console.log('1. Install the MCP server in Claude Desktop');
console.log('2. Update Claude Desktop MCP configuration');
console.log('3. Restart Claude Desktop to load new tools');
console.log('4. Test multimedia features with sample files');