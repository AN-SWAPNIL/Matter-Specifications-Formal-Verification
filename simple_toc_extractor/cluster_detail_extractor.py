#!/usr/bin/env python3
"""
Enhanced Matter Cluster Detail Extractor with Section-Based Approach
Follows existing RAG pattern but uses targeted section extr        try:
            # Add buffer pages and convert to 0-indexed for PyMuPDF
            actual_start = max(0, start_page - SUBSECTION_PAGE_BUFFER - 1)
            actual_end = min(len(self.pdf_doc), end_page + SUBSECTION_PAGE_BUFFER)
            
            text_content_parts = []
            for page_num in range(actual_start, actual_end):
                page = self.pdf_doc.load_page(page_num)
                text = page.get_text()
                # Add page markers for better context tracking
                text_content_parts.append(f"--- Page {page_num + 1} (Content Page {page_num + 1 - PDF_PAGE_OFFSET}) ---\n{text}")
            
            text_content = "\n\n".join(text_content_parts)
            logger.info(f"Extracted subsection '{subsection_name}' from PDF pages {actual_start+1}-{actual_end} (content pages {start_page}-{end_page}) ({len(text_content)} characters)")
            return text_contentgher accuracy
"""

import json
import logging
import os
import sys
import signal
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import fitz  # PyMuPDF
import pymupdf4llm  # Smart table extraction in Markdown format
from langchain_google_genai import GoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from config import (
    GOOGLE_API_KEY, GEMINI_MODEL, GEMINI_TEMPERATURE, GEMINI_MAX_OUTPUT_TOKENS,
    CLUSTER_PAGE_BUFFER, PDF_PAGE_OFFSET, EMBEDDINGS_MODEL, CHUNK_SIZE, CHUNK_OVERLAP, VECTOR_SEARCH_K, SUBSECTION_PAGE_BUFFER,
    section_prompt_dict
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedClusterExtractor:
    """Enhanced cluster extractor using section-based approach with RAG foundation"""
    
    def __init__(self, pdf_path: str, clusters_json_path: str, output_path: str = "matter_clusters_enhanced.json"):
        """
        Initialize the enhanced cluster extractor
        
        Args:
            pdf_path: Path to the Matter specification PDF
            clusters_json_path: Path to the clusters TOC JSON file
            output_path: Path to output JSON file
        """
        self.pdf_path = pdf_path
        self.clusters_json_path = clusters_json_path
        self.output_path = output_path
        self.pdf_doc = None
        self.llm = None
        self.embeddings = None
        self.clusters_data = None
        self.current_results = None
        self.interruption_handler_set = False
        
        # Initialize components
        self._load_pdf()
        self._init_llm()
        self._load_clusters_data()
        self._setup_interruption_handler()
    
    def _setup_interruption_handler(self):
        """Setup signal handlers for graceful interruption"""
        if not self.interruption_handler_set:
            def signal_handler(signum, frame):
                logger.warning(f"Received signal {signum}. Saving current progress...")
                self._save_current_progress()
                sys.exit(0)
            
            signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
            signal.signal(signal.SIGTERM, signal_handler)  # Termination
            self.interruption_handler_set = True
            logger.info("Interruption handlers set up for fail-safe operation")
    
    def _save_current_progress(self):
        """Save current progress to output file"""
        if self.current_results and len(self.current_results.get('clusters', [])) > 0:
            try:
                backup_path = f"{self.output_path}.backup"
                with open(backup_path, 'w', encoding='utf-8') as f:
                    json.dump(self.current_results, f, indent=2, ensure_ascii=False)
                logger.info(f"Progress saved to {backup_path}")
                
                # Also save to main output file
                with open(self.output_path, 'w', encoding='utf-8') as f:
                    json.dump(self.current_results, f, indent=2, ensure_ascii=False)
                logger.info(f"Progress saved to {self.output_path}")
            except Exception as e:
                logger.error(f"Error saving progress: {e}")
    
    def load_existing_results(self) -> Dict[str, Any]:
        """Load existing results from output file if it exists"""
        if os.path.exists(self.output_path):
            try:
                with open(self.output_path, 'r', encoding='utf-8') as f:
                    existing_results = json.load(f)
                logger.info(f"Loaded existing results with {len(existing_results.get('clusters', []))} clusters")
                return existing_results
            except Exception as e:
                logger.warning(f"Error loading existing results: {e}")
        return None
    
    def get_processed_section_numbers(self, existing_results: Dict[str, Any]) -> set:
        """Get set of already processed section numbers"""
        processed = set()
        if existing_results and 'clusters' in existing_results:
            for cluster in existing_results['clusters']:
                metadata = cluster.get('metadata', {})
                section_num = metadata.get('section_number')
                if section_num:
                    processed.add(section_num)
        logger.info(f"Found {len(processed)} already processed clusters: {sorted(processed)}")
        return processed
    
    def _load_pdf(self):
        """Load the PDF document"""
        try:
            self.pdf_doc = fitz.open(self.pdf_path)
            logger.info(f"Loaded PDF with {len(self.pdf_doc)} pages")
        except Exception as e:
            logger.error(f"Error loading PDF: {e}")
            raise
    
    def _init_llm(self):
        """Initialize the language model and embeddings"""
        try:
            self.llm = GoogleGenerativeAI(
                model=GEMINI_MODEL,
                google_api_key=GOOGLE_API_KEY,
                temperature=GEMINI_TEMPERATURE
            )
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model="models/embedding-001",
                google_api_key=GOOGLE_API_KEY
            )
            logger.info("Initialized Gemini LLM and embeddings")
        except Exception as e:
            logger.error(f"Error initializing LLM: {e}")
            raise
    
    def _load_clusters_data(self):
        """Load clusters data from JSON file"""
        try:
            with open(self.clusters_json_path, 'r', encoding='utf-8') as f:
                self.clusters_data = json.load(f)
            logger.info(f"Loaded {len(self.clusters_data.get('clusters', {}))} clusters")
        except Exception as e:
            logger.error(f"Error loading clusters data: {e}")
            raise
    
    def extract_pages_markdown(self, start_page: int, end_page: int, context: str = "") -> str:
        """
        Extract PDF pages in Markdown format for better table understanding
        Uses PyMuPDF4LLM for smart table extraction
        
        Args:
            start_page: Starting page number (0-indexed for PyMuPDF)
            end_page: Ending page number (0-indexed for PyMuPDF)
            context: Context description for logging (e.g., cluster name, subsection name)
            
        Returns:
            Extracted text in Markdown format with preserved table structure
        """
        try:
            # Extract pages in Markdown format for better table structure
            page_list = list(range(start_page, end_page))
            md_text = pymupdf4llm.to_markdown(
                self.pdf_path,
                pages=page_list,
                page_chunks=False  # Get continuous text
            )
            
            # Add context markers for better tracking
            text_parts = [
                f"--- Pages {start_page+1}-{end_page} | Context: {context} ---",
                "**Tables formatted in Markdown for optimal LLM understanding**\n",
                md_text
            ]
            text_content = "\n\n".join(text_parts)
            
            logger.info(f"✓ Extracted Markdown from pages {start_page+1}-{end_page} for '{context}' ({len(text_content)} chars)")
            return text_content
            
        except Exception as e:
            logger.error(f"Error extracting Markdown from pages {start_page+1}-{end_page} for '{context}': {e}")
            return ""
    
    def extract_cluster_pages(self, start_page: int, end_page: int) -> str:
        """
        Extract text content from PDF pages for a specific cluster
        Uses PyMuPDF4LLM Markdown format for superior table extraction
        
        Args:
            start_page: Starting page number (1-indexed)
            end_page: Ending page number (1-indexed)
            
        Returns:
            Extracted text content in Markdown format
        """
        try:
            # Add buffer pages and convert to 0-indexed for PyMuPDF
            actual_start = max(0, start_page - CLUSTER_PAGE_BUFFER - 1)
            actual_end = min(len(self.pdf_doc), end_page + CLUSTER_PAGE_BUFFER)
            
            # Use dedicated Markdown extraction method
            context = f"Cluster pages {start_page}-{end_page}"
            return self.extract_pages_markdown(actual_start, actual_end, context)
            
        except Exception as e:
            logger.error(f"Error extracting pages {start_page}-{end_page}: {e}")
            return ""
    
    def create_vector_store(self, text_content: str) -> Optional[FAISS]:
        """
        Create a vector store from text content using same approach as original
        
        Args:
            text_content: Text content to vectorize
            
        Returns:
            FAISS vector store or None if failed
        """
        try:
            # Split text into chunks optimized for technical specifications and tables
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=CHUNK_SIZE,
                chunk_overlap=CHUNK_OVERLAP,
                separators=[
                    "\n\n\n\n",  # Major section breaks (multiple newlines)
                    "\n\n\n",    # Section breaks  
                    "\n\n",      # Paragraph breaks
                    "\n",        # Line breaks
                    ".",         # Sentence breaks
                    " ",         # Word breaks
                ],
                length_function=len,
                keep_separator=True  # Keep separators to maintain table structure
            )
            
            chunks = text_splitter.split_text(text_content)
            documents = [Document(page_content=chunk) for chunk in chunks]
            
            logger.info(f"Created {len(documents)} text chunks for vectorization")
            
            # Create vector store
            vector_store = FAISS.from_documents(documents, self.embeddings)
            logger.info("Successfully created vector store")
            
            return vector_store
            
        except Exception as e:
            logger.error(f"Error creating vector store: {e}")
            return None
    
    def extract_subsection_pages(self, start_page: int, end_page: int, subsection_name: str = "") -> str:
        """
        Extract text content from PDF pages for a specific subsection
        Uses PyMuPDF4LLM Markdown format for superior table extraction
        
        Args:
            start_page: Starting page number (1-indexed)
            end_page: Ending page number (1-indexed)
            subsection_name: Name of subsection for logging
            
        Returns:
            Extracted subsection text content in Markdown format
        """
        try:
            # Add buffer pages and convert to 0-indexed for PyMuPDF
            actual_start = max(0, start_page - SUBSECTION_PAGE_BUFFER - 1)
            actual_end = min(len(self.pdf_doc), end_page + SUBSECTION_PAGE_BUFFER)
            
            # Use dedicated Markdown extraction method
            context = f"Subsection '{subsection_name}'"
            return self.extract_pages_markdown(actual_start, actual_end, context)
            
        except Exception as e:
            logger.error(f"Error extracting subsection pages {start_page}-{end_page} for {subsection_name}: {e}")
            return ""
    
    def extract_subsection_text_from_json(self, cluster_data: Dict[str, Any], subsection_type: str) -> str:
        """
        Extract subsection text based on JSON subsection data
        
        Args:
            cluster_data: Cluster information from matter_clusters_toc.json
            subsection_type: Type of subsection to extract (e.g., 'Revision History', 'Features', etc.)
            
        Returns:
            Extracted subsection text
        """
        try:
            subsections = cluster_data.get('subsections', [])
            cluster_name = cluster_data.get('cluster_name', 'Unknown')
            
            # Find matching subsection by name
            logger.debug(f"Looking for {subsection_type} in {len(subsections)} subsections for {cluster_name}")
            for i, subsection in enumerate(subsections):
                subsection_name = subsection.get('subsection_name', '')
                logger.debug(f"  Subsection {i+1}: '{subsection_name}'")
                if subsection_name.lower() == subsection_type.lower():
                    start_page = subsection.get('start_page')
                    end_page = subsection.get('end_page')
                    
                    if start_page and end_page:
                        logger.info(f"Found exact match: Extracting {subsection_type} for {cluster_name} from pages {start_page}-{end_page}")
                        return self.extract_subsection_pages(start_page, end_page, f"{cluster_name} - {subsection_type}")
            
            # If exact match not found, try partial matches for common variations
            subsection_variations = {
                'revision history': ['revision history', 'revision_history', 'history'],
                'classification': ['classification'],
                'cluster id': ['cluster id', 'cluster_id', 'cluster ids'],
                'features': ['features', 'feature'],
                'data types': ['data types', 'data_types', 'types'],
                'attributes': ['attributes', 'attribute'],
                'commands': ['commands', 'command'],
                'events': ['events', 'event']
            }
            
            search_terms = subsection_variations.get(subsection_type.lower(), [subsection_type.lower()])
            
            for subsection in subsections:
                subsection_name = subsection.get('subsection_name', '').lower()
                for term in search_terms:
                    if term in subsection_name:
                        start_page = subsection.get('start_page')
                        end_page = subsection.get('end_page')
                        
                        if start_page and end_page:
                            logger.info(f"Found {subsection_type} match: '{subsection.get('subsection_name')}' for {cluster_name} from pages {start_page}-{end_page}")
                            return self.extract_subsection_pages(start_page, end_page, f"{cluster_name} - {subsection_type}")
            
            logger.warning(f"No {subsection_type} subsection found for {cluster_name}")
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting {subsection_type} subsection text: {e}")
            return ""
    
    def extract_section_with_direct_text(self, cluster_data: Dict[str, Any], section_prompt: str, section_type: str, cluster_name: str = "") -> Optional[Any]:
        """
        Extract section information using direct PDF text extraction from subsection pages
        
        Args:
            cluster_data: Cluster information from matter_clusters_toc.json
            section_prompt: Specialized prompt for this section type
            section_type: Type of subsection to extract (e.g., 'Revision History', 'Features', etc.)
            cluster_name: Name of cluster for context
            
        Returns:
            Extracted section information
        """
        try:
            # Extract section text directly from PDF pages using JSON subsection data
            section_text = self.extract_subsection_text_from_json(cluster_data, section_type)
            
            if not section_text:
                logger.warning(f"No {section_type} subsection found for {cluster_name}, skipping")
                return []  # Return empty array when no subsection found
            
            # Use the specialized prompt with section text appended at the end
            # Add section context and cluster information
            section_context = f"\n\n**SECTION TO EXTRACT FROM:**\n{section_type} section from {cluster_name}\n\n**SECTION TEXT:**\n{section_text}"
            final_prompt = section_prompt + section_context
            
            logger.info(f"Extracting {section_type} for {cluster_name} using direct PDF text (text length: {len(section_text)})")
            
            # Get LLM response
            response = self.llm.invoke(final_prompt)
            
            # Clean up response before JSON parsing
            # Remove markdown code blocks
            response = re.sub(r'```json\s*', '', response)
            response = re.sub(r'```\s*', '', response)
            
            # Remove any leading/trailing explanatory text
            response = response.strip()
            
            # Check if response looks truncated (similar to old implementation)
            if len(response) > 30000 and not response.endswith(('}', ']')):
                logger.warning(f"Response for {section_type} in {cluster_name} appears truncated ({len(response)} chars)")
                # The JSON repair method will handle truncated responses
            
            # Try to parse JSON response
            try:
                result = json.loads(response)
                logger.info(f"Successfully extracted {section_type} for {cluster_name} from direct PDF text")
                return result
            except json.JSONDecodeError as e:
                # Log the actual response for debugging
                logger.warning(f"JSON parsing failed for {section_type} in {cluster_name}: {e}")
                logger.debug(f"Raw response preview: {response[:500]}...")
                
                # Try to repair the JSON
                logger.warning(f"Attempting repair for {section_type} in {cluster_name}...")
                repaired_result = self._attempt_json_repair(response, section_type, cluster_name)
                if repaired_result:
                    logger.info(f"Successfully repaired JSON for {section_type} in {cluster_name}")
                    return repaired_result
                
                logger.error(f"Failed to parse {section_type} response for {cluster_name}")
                # Return empty array for list-type sections instead of None
                if section_type.lower() in ['revision history', 'features', 'data types', 'attributes', 'commands', 'events']:
                    logger.warning(f"Returning empty array for {section_type} in {cluster_name}")
                    return []
                return None
                
        except Exception as e:
            logger.error(f"Error extracting {section_type} for {cluster_name}: {e}")
            return None
    
    def _attempt_json_repair(self, response: str, section_type: str, cluster_name: str) -> Optional[Any]:
        """
        Attempt to repair malformed JSON response with improved strategies
        
        Args:
            response: Raw LLM response
            section_type: Type of section being extracted
            cluster_name: Name of cluster for logging
            
        Returns:
            Parsed JSON if repair successful, None otherwise
        """
        try:
            original_response = response
            
            # Remove markdown code blocks
            response = re.sub(r'```json\s*', '', response)
            response = re.sub(r'```\s*', '', response)
            
            # Remove any leading/trailing explanatory text
            response = response.strip()
            
            # Try multiple JSON extraction strategies (reordered by success rate)
            strategies = [
                # Strategy 1 (previously 2): Find JSON starting with array/object - MOST SUCCESSFUL
                lambda s: re.search(r'([\[\{].*)', s, re.DOTALL),
                
                # Strategy 2 (previously 1): Find complete JSON array/object
                lambda s: re.search(r'(\[.*\])', s, re.DOTALL),
                lambda s: re.search(r'(\{.*\})', s, re.DOTALL),
                
                # Strategy 3: Look for anything between brackets
                lambda s: re.search(r'.*?(\[.*\]).*?', s, re.DOTALL),
                lambda s: re.search(r'.*?(\{.*\}).*?', s, re.DOTALL),
            ]
            
            for i, strategy in enumerate(strategies):
                try:
                    match = strategy(response)
                    if match:
                        json_str = match.group(1).strip()
                        
                        # Clean up JSON string before parsing
                        # Remove markdown code blocks
                        json_str = re.sub(r'```json\s*', '', json_str)
                        json_str = re.sub(r'```\s*', '', json_str)
                        
                        # Remove any leading/trailing explanatory text
                        json_str = json_str.strip()
                        
                        # Try to parse the extracted JSON
                        result = json.loads(json_str)
                        logger.info(f"JSON repair successful using strategy {i+1} for {section_type} in {cluster_name}")
                        return result
                        
                except (json.JSONDecodeError, AttributeError) as e:
                    continue
            
            # If all strategies fail, try advanced repair techniques from old implementation
            try:
                # Clean response
                clean_response = response.strip()
                if clean_response.startswith('```json'):
                    clean_response = clean_response[7:]
                if clean_response.endswith('```'):
                    clean_response = clean_response[:-3]
                clean_response = clean_response.strip()
                
                # Strategy 1: Find the last complete JSON structure using brace counting
                brace_count = 0
                last_valid_pos = 0
                in_string = False
                escape_next = False
                
                for i, char in enumerate(clean_response):
                    if escape_next:
                        escape_next = False
                        continue
                        
                    if char == '\\':
                        escape_next = True
                        continue
                        
                    if char == '"' and not escape_next:
                        in_string = not in_string
                        continue
                        
                    if not in_string:
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                last_valid_pos = i + 1
                                break
                
                if last_valid_pos > 0:
                    truncated_response = clean_response[:last_valid_pos]
                    logger.info(f"Attempting to parse truncated JSON for {section_type} in {cluster_name} (length: {last_valid_pos})")
                    result = json.loads(truncated_response)
                    return result
                
                # Strategy 2: Try to close unclosed braces
                open_braces = clean_response.count('{') - clean_response.count('}')
                if open_braces > 0:
                    repaired_response = clean_response + '}' * open_braces
                    logger.info(f"Attempting to close {open_braces} unclosed braces for {section_type} in {cluster_name}")
                    result = json.loads(repaired_response)
                    return result
                
                # Strategy 3: For array responses, try to extract complete array
                if section_type.lower() in ['data_types', 'attributes', 'commands', 'events', 'features']:
                    bracket_start = clean_response.find('[')
                    if bracket_start >= 0:
                        bracket_count = 0
                        end_pos = bracket_start
                        in_string = False
                        escape_next = False
                        
                        for i in range(bracket_start, len(clean_response)):
                            char = clean_response[i]
                            if escape_next:
                                escape_next = False
                                continue
                                
                            if char == '\\':
                                escape_next = True
                                continue
                                
                            if char == '"' and not escape_next:
                                in_string = not in_string
                                continue
                                
                            if not in_string:
                                if char == '[':
                                    bracket_count += 1
                                elif char == ']':
                                    bracket_count -= 1
                                    if bracket_count == 0:
                                        end_pos = i + 1
                                        break
                        
                        if bracket_count == 0:
                            array_json = clean_response[bracket_start:end_pos]
                            logger.info(f"Attempting to extract complete array for {section_type} in {cluster_name}")
                            result = json.loads(array_json)
                            return result
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.debug(f"Advanced JSON repair failed for {section_type} in {cluster_name}: {e}")
            
            # If all strategies fail, try to parse the entire response
            try:
                # Clean up response before JSON parsing
                clean_response = response
                # Remove markdown code blocks
                clean_response = re.sub(r'```json\s*', '', clean_response)
                clean_response = re.sub(r'```\s*', '', clean_response)
                
                # Remove any leading/trailing explanatory text
                clean_response = clean_response.strip()
                
                result = json.loads(clean_response)
                logger.info(f"JSON repair successful with direct parsing for {section_type} in {cluster_name}")
                return result
            except json.JSONDecodeError:
                pass
            
            # Last resort: return empty array for list sections
            if section_type.lower() in ['data_types', 'attributes', 'commands', 'events', 'features']:
                logger.warning(f"Returning empty array for {section_type} in {cluster_name} due to JSON repair failure")
                return []
            
            logger.warning(f"Could not repair JSON for {section_type} in {cluster_name}")
            logger.debug(f"Original response: {original_response[:1000]}...")
            return None
            
        except Exception as e:
            logger.error(f"JSON repair failed for {section_type} in {cluster_name}: {e}")
            return None
    



    def process_cluster_enhanced(self, cluster_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single cluster using enhanced section-based approach
        
        Args:
            cluster_data: Cluster information from TOC
            
        Returns:
            Extracted cluster information with same structure as original
        """
        cluster_name = cluster_data.get('cluster_name', 'Unknown')
        section_number = cluster_data.get('section_number', 'Unknown')
        start_page = cluster_data.get('start_page', 1)
        end_page = cluster_data.get('end_page', 1)
        category = cluster_data.get('category', 'Unknown')
        subsections = cluster_data.get('subsections', [])
        
        logger.info(f"Processing cluster: {cluster_name} ({section_number}) pages {start_page}-{end_page} with {len(subsections)} subsections")
        
        # # Extract full cluster text for fallback only
        # cluster_text = self.extract_cluster_pages(start_page, end_page)
        # if not cluster_text:
        #     logger.error(f"Failed to extract text for {cluster_name}")
        #     return None
        
        # Initialize cluster info with cluster_name from TOC at the top
        # This provides the cluster name from matter_clusters_toc.json
        cluster_info = {
            "cluster_name": cluster_name
        }
        
        # Track all references across all sections
        all_references = []
        
        # Track if we've already processed cluster overview (ID + Classification)
        cluster_overview_processed = False
        
        # Dynamically extract all subsections using section_prompt_dict
        for subsection in subsections:
            subsection_name = subsection.get('subsection_name', '')
            
            # Get the appropriate prompt from section_prompt_dict
            if subsection_name not in section_prompt_dict:
                logger.warning(f"No prompt found for subsection '{subsection_name}' in {cluster_name}, skipping")
                continue
            
            # OPTIMIZATION: Cluster ID/IDs and Classification use the same prompt (CLUSTER_OVERVIEW_EXTRACTION_PROMPT)
            # Make a single AI call for both instead of separate calls
            if subsection_name in ['Cluster ID', 'Classification', 'Cluster IDs']:
                if cluster_overview_processed:
                    logger.info(f"⚡ Skipping '{subsection_name}' - already extracted with cluster overview (single AI call optimization)")
                    continue
                else:
                    logger.info(f"⚡ Processing cluster overview (ID + Classification) with single AI call for {cluster_name}")
                    cluster_overview_processed = True
            
            section_prompt = section_prompt_dict[subsection_name]
            
            # Extract the subsection data
            result = self.extract_section_with_direct_text(cluster_data, section_prompt, subsection_name, cluster_name)

            """
            # Log extracted data with safe preview
            if result:
                try:
                    if isinstance(result, (str, list)):
                        preview = str(result)[0:min(len(str(result)), 100)] + "..." if len(str(result)) > 100 else str(result)
                    elif isinstance(result, dict):
                        preview = str(result)[0:min(len(str(result)), 100)] + "..." if len(str(result)) > 100 else str(result)
                    else:
                        preview = str(result)[0:min(len(str(result)), 100)] + "..." if len(str(result)) > 100 else str(result)
                    logger.info(f"Extracted data for subsection '{subsection_name}' in {cluster_name}: {preview}")
                except Exception as e:
                    logger.info(f"Extracted data for subsection '{subsection_name}' in {cluster_name}: [Data extracted but preview failed: {e}]")
            else:
                logger.info(f"No data extracted for subsection '{subsection_name}' in {cluster_name}")
            """

            if result is None:
                continue
            
            # Handle different response formats
            # Special handling for Cluster ID and Classification (combined in CLUSTER_OVERVIEW_EXTRACTION_PROMPT)
            if subsection_name in ['Cluster ID', 'Classification', 'Cluster IDs']:
                if isinstance(result, dict):
                    # Extract cluster_ids array and store in subsection
                    cluster_ids = result.get('cluster_ids', [])
                    if cluster_ids:
                        cluster_info['cluster_id'] = cluster_ids
                    
                    # Extract classifications array and store in subsection
                    classifications = result.get('classifications', [])
                    if classifications:
                        cluster_info['classification'] = classifications
                    
                    # Collect references
                    all_references.extend(result.get('references', []))
                else:
                    # Fallback for old format or unexpected structure
                    # Map old field names to new field names
                    if subsection_name in ['Cluster ID', 'Cluster IDs']:
                        cluster_info['cluster_id'] = result
                    elif subsection_name == 'Classification':
                        cluster_info['classification'] = result
                    else:
                        cluster_info[subsection_name] = result
            
            # Handle Revision History
            elif subsection_name == 'Revision History':
                if isinstance(result, dict):
                    cluster_info['revision_history'] = result.get('revisions', [])
                    all_references.extend(result.get('references', []))
                elif isinstance(result, list):
                    cluster_info['revision_history'] = result
                else:
                    cluster_info['revision_history'] = []
            
            # Handle Features
            elif subsection_name == 'Features':
                if isinstance(result, dict):
                    cluster_info['features'] = result.get('features', [])
                    all_references.extend(result.get('references', []))
                elif isinstance(result, list):
                    cluster_info['features'] = result
                else:
                    cluster_info['features'] = []
            
            # Handle Data Types
            elif subsection_name == 'Data Types':
                if isinstance(result, dict):
                    cluster_info['data_types'] = result.get('data_types', [])
                    all_references.extend(result.get('references', []))
                elif isinstance(result, list):
                    cluster_info['data_types'] = result
                else:
                    cluster_info['data_types'] = []
            
            # Handle Attributes
            elif subsection_name == 'Attributes':
                if isinstance(result, dict):
                    cluster_info['attributes'] = result.get('attributes', [])
                    all_references.extend(result.get('references', []))
                elif isinstance(result, list):
                    cluster_info['attributes'] = result
                else:
                    cluster_info['attributes'] = []
            
            # Handle Commands
            elif subsection_name == 'Commands':
                if isinstance(result, dict):
                    cluster_info['commands'] = result.get('commands', [])
                    all_references.extend(result.get('references', []))
                elif isinstance(result, list):
                    cluster_info['commands'] = result
                else:
                    cluster_info['commands'] = []
            
            # Handle Events
            elif subsection_name == 'Events':
                if isinstance(result, dict):
                    cluster_info['events'] = result.get('events', [])
                    all_references.extend(result.get('references', []))
                elif isinstance(result, list):
                    cluster_info['events'] = result
                else:
                    cluster_info['events'] = []
            
            # Handle all other subsection types dynamically
            else:
                # Store the extracted data using the subsection name as key
                if isinstance(result, dict):
                    # Extract references if present
                    refs = result.get('references', [])
                    if refs:
                        all_references.extend(refs)
                        # Remove references from the main data to avoid duplication
                        result_copy = result.copy()
                        result_copy.pop('references', None)
                        cluster_info[subsection_name] = result_copy
                    else:
                        cluster_info[subsection_name] = result
                else:
                    # For list or other types, store directly
                    cluster_info[subsection_name] = result
            
            logger.info(f"Successfully extracted '{subsection_name}' for {cluster_name}")
        
        # Deduplicate references by name
        unique_references = {}
        for ref in all_references:
            ref_name = ref.get('name', '')
            if ref_name and ref_name not in unique_references:
                unique_references[ref_name] = ref
        
        # Add references to cluster_info
        cluster_info['references'] = list(unique_references.values())
        
        # Ensure required fields exist with defaults if not extracted
        if 'revision_history' not in cluster_info:
            cluster_info['revision_history'] = []
        if 'features' not in cluster_info:
            cluster_info['features'] = []
        if 'data_types' not in cluster_info:
            cluster_info['data_types'] = []
        if 'attributes' not in cluster_info:
            cluster_info['attributes'] = []
        if 'commands' not in cluster_info:
            cluster_info['commands'] = []
        if 'events' not in cluster_info:
            cluster_info['events'] = []
        
        return {
            "cluster_info": cluster_info,
            "metadata": {
                "source_pages": f"{start_page}-{end_page}",
                "extraction_method": "enhanced_section_based_dynamic",
                # "text_length": len(cluster_text),
                "section_number": section_number,
                "category": category,
                "subsections_processed": len([s for s in subsections if s.get('subsection_name') in section_prompt_dict])
            }
        }
    
    def validate_and_enhance_cluster(self, cluster_result: Dict[str, Any], full_cluster_text: str) -> Dict[str, Any]:
        """
        Final validation step to check consistency and fill gaps without reducing information
        
        Args:
            cluster_result: Extracted cluster information
            full_cluster_text: Complete cluster text for reference
            
        Returns:
            Enhanced and validated cluster information
        """
        validation_prompt = f"""
You are validating extracted Matter cluster information for accuracy and completeness.

**TASK**: Review the extracted data against the full specification text and enhance without reducing information.

**EXTRACTED DATA**:
{json.dumps(cluster_result, indent=2)}

**FULL CLUSTER TEXT**:
{full_cluster_text}...

**VALIDATION REQUIREMENTS**:
1. **Accuracy Check**: Verify all extracted information matches the specification
2. **Completeness Check**: Add any missing information found in the text  
3. **Consistency Check**: Ensure data types, IDs, and references are consistent
4. **Enhancement**: Add missing details WITHOUT removing existing information
5. **Pseudocode**: Ensure command "effect_on_receipt" includes pseudocode format

**CRITICAL**: Do NOT remove or reduce any existing information. Only add and enhance.

Return the COMPLETE enhanced cluster JSON structure with the same format.
"""
        
        try:
            response = self.llm.invoke(validation_prompt)
            
            # Clean up response before JSON parsing
            # Remove markdown code blocks
            response = re.sub(r'```json\s*', '', response)
            response = re.sub(r'```\s*', '', response)
            
            # Remove any leading/trailing explanatory text
            response = response.strip()
            
            # Try to parse the enhanced result
            try:
                enhanced_result = json.loads(response)
                logger.info(f"Successfully enhanced cluster: {cluster_result['cluster_info']['cluster_name']}")
                return enhanced_result
            except json.JSONDecodeError:
                # If validation fails, return original
                logger.warning(f"Validation enhancement failed, returning original for: {cluster_result['cluster_info']['cluster_name']}")
                return cluster_result
                
        except Exception as e:
            logger.error(f"Error in validation enhancement: {e}")
            return cluster_result
    

    
    def process_all_clusters(self, limit: Optional[int] = None, resume: bool = True) -> Dict[str, Any]:
        """
        Process all clusters using enhanced section-based extraction
        
        Args:
            limit: Maximum number of clusters to process (None for all)
            resume: Whether to resume from existing results
            
        Returns:
            Complete extraction results
        """
        # Load existing results if resuming (same as original logic)
        existing_results = None if not resume else self.load_existing_results()
        processed_sections = set() if not existing_results else self.get_processed_section_numbers(existing_results)
        
        # Initialize results structure (same as original)
        if existing_results and resume:
            results = existing_results
        else:
            results = {
                "extraction_info": {
                    "total_clusters": 0,
                    "pdf_source": self.pdf_path,
                    "extraction_timestamp": datetime.now().isoformat(),
                    "extraction_method": "enhanced_section_based"
                },
                "clusters": []
            }
        
        self.current_results = results
        
        clusters_to_process = list(self.clusters_data.get('clusters', {}).items())
        total_clusters = len(clusters_to_process)
        
        if limit:
            clusters_to_process = clusters_to_process[:limit]
        
        logger.info(f"Processing {len(clusters_to_process)} clusters out of {total_clusters}")
        
        processed_count = len([c for c in results['clusters']])
        
        for cluster_key, cluster_data in clusters_to_process:
            section_number = cluster_data.get('section_number', cluster_key)
            
            # Skip if already processed
            if resume and section_number in processed_sections:
                logger.info(f"Skipping already processed cluster: {section_number}")
                continue
            
            try:
                # Process cluster using enhanced approach
                cluster_result = self.process_cluster_enhanced(cluster_data)
                
                # Skip if cluster processing failed (returns None)
                if cluster_result is None:
                    logger.warning(f"Skipping cluster {section_number} due to processing failure")
                    continue
                
                """
                # Extract full cluster text for final validation
                start_page = cluster_data.get('start_page', 1)
                end_page = cluster_data.get('end_page', 1)
                full_cluster_text = self.extract_cluster_pages(start_page, end_page)
                
                # Final validation and enhancement step
                if full_cluster_text:
                    cluster_result = self.validate_and_enhance_cluster(cluster_result, full_cluster_text)
                """
                
                # Add to results
                results['clusters'].append(cluster_result)
                processed_count += 1
                
                # Update extraction info
                results['extraction_info']['total_clusters'] = processed_count
                results['extraction_info']['extraction_timestamp'] = datetime.now().isoformat()
                
                # Save progress periodically
                if processed_count % 5 == 0:
                    self._save_current_progress()
                
                logger.info(f"Successfully processed cluster {processed_count}: {cluster_data.get('cluster_name', 'Unknown')}")
                
            except KeyboardInterrupt:
                logger.warning("Processing interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error processing cluster {section_number}: {e}")
                # Skip failed cluster instead of adding fallback
                continue
        
        # Final save
        self._save_current_progress()
        
        logger.info(f"Completed processing {processed_count} clusters")
        return results
    
    def save_results(self, results: Dict[str, Any], output_path: str):
        """Save extraction results to JSON file (same as original)"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"Results saved to {output_path}")
        except Exception as e:
            logger.error(f"Error saving results: {e}")


def main():
    """Main function"""
    # File paths - PDF is in parent directory
    pdf_path = os.path.join("..", "Matter-1.4-Application-Cluster-Specification.pdf")
    clusters_json_path = "matter_clusters_toc.json"
    output_path = "matter_clusters_enhanced.json"
    
    # Check if files exist
    if not os.path.exists(clusters_json_path):
        logger.error(f"Clusters JSON file not found: {clusters_json_path}")
        logger.info("Please run the TOC extractor first to generate the clusters JSON file")
        return
    
    # Check if PDF exists
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        logger.info("Please ensure the Matter-1.4-Application-Cluster-Specification.pdf is in the parent directory")
        return
    
    try:
        # Initialize enhanced extractor
        logger.info("Initializing Enhanced Cluster Extractor with section-based approach...")
        extractor = EnhancedClusterExtractor(pdf_path, clusters_json_path, output_path)
        
        # Process clusters (test with first few)
        logger.info("Starting enhanced cluster extraction with specialized section prompts...")
        results = extractor.process_all_clusters(limit=1, resume=True)
        
        # Save final results
        extractor.save_results(results, output_path)
        
        logger.info("Enhanced cluster extraction completed successfully!")
        logger.info(f"Results saved to: {output_path}")
        logger.info(f"Processed {len(results.get('clusters', []))} clusters with enhanced accuracy")
        
    except ImportError as e:
        logger.error(f"Missing dependencies: {e}")
        logger.info("Please install required packages: pip install PyMuPDF langchain langchain-google-genai faiss-cpu sentence-transformers")
    except KeyboardInterrupt:
        logger.warning("Extraction interrupted by user")
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    
    finally:
        logger.info("Enhanced cluster extraction finished")
        

if __name__ == "__main__":
    main()