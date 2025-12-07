#!/usr/bin/env python3
"""
Enhanced Matter Cluster Detail Extractor with Section-Based Approach
Uses direct PDF extraction with LLM-based processing for cluster information
"""

import json
import logging
import os
import sys
import signal
import re
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import fitz  # PyMuPDF
import pymupdf4llm  # Smart table extraction in Markdown format
from langchain.chat_models import init_chat_model
from config import (
    API_KEY, LLM_MODEL, MODEL_PROVIDER, LLM_TEMPERATURE, LLM_MAX_OUTPUT_TOKENS,
    CLUSTER_PAGE_BUFFER, SUBSECTION_PAGE_BUFFER, section_prompt_dict
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedClusterExtractor:
    """Enhanced cluster extractor using section-based approach with direct LLM processing"""
    
    def __init__(self, pdf_path: str, clusters_json_path: str, output_dir: str = "cluster_details"):
        """
        Initialize the enhanced cluster extractor
        
        Args:
            pdf_path: Path to the Matter specification PDF
            clusters_json_path: Path to the clusters TOC JSON file
            output_dir: Directory to save individual cluster JSON files
        """
        self.pdf_path = pdf_path
        self.clusters_json_path = clusters_json_path
        self.output_dir = output_dir
        self.pdf_doc = None
        self.llm = None
        self.clusters_data = None
        self.interruption_handler_set = False
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize components
        self._load_pdf()
        self._init_llm()
        self._load_clusters_data()
        self._setup_interruption_handler()
    
    def _setup_interruption_handler(self):
        """Setup signal handlers for graceful interruption"""
        if not self.interruption_handler_set:
            def signal_handler(signum, frame):
                logger.warning(f"Received signal {signum}. Exiting gracefully...")
                sys.exit(0)
            
            signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
            signal.signal(signal.SIGTERM, signal_handler)  # Termination
            self.interruption_handler_set = True
            logger.info("Interruption handlers set up")
    
    def save_cluster_to_file(self, cluster_result: Dict[str, Any], cluster_name: str, section_number: str) -> str:
        """
        Save individual cluster to a separate JSON file.
        
        Args:
            cluster_result: Extracted cluster information
            cluster_name: Name of the cluster
            section_number: Section number for filename
            
        Returns:
            Path to saved file
        """
        try:
            # Sanitize cluster name for filename (matching llm_as_judge.py)
            safe_cluster_name = "".join(c for c in cluster_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_cluster_name = safe_cluster_name.replace(' ', '_')
            
            # Create filename with section number (matching format: {section}_{name}_detail.json)
            if section_number:
                filename = f"{section_number}_{safe_cluster_name}_detail.json"
            else:
                filename = f"{safe_cluster_name}_detail.json"
            
            filepath = os.path.join(self.output_dir, filename)
            
            # Save cluster to individual file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(cluster_result, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✓ Saved: {filename}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving cluster to file: {e}")
            return None
    
    def _load_pdf(self):
        """Load the PDF document"""
        try:
            self.pdf_doc = fitz.open(self.pdf_path)
            logger.info(f"Loaded PDF with {len(self.pdf_doc)} pages")
        except Exception as e:
            logger.error(f"Error loading PDF: {e}")
            raise
    
    def _init_llm(self):
        """Initialize the language model"""
        if not os.environ.get("GOOGLE_API_KEY"):
            os.environ["GOOGLE_API_KEY"] = API_KEY
        
        try:
            self.llm = init_chat_model(
                LLM_MODEL,
                model_provider=MODEL_PROVIDER,
                temperature=LLM_TEMPERATURE,
                max_tokens=LLM_MAX_OUTPUT_TOKENS
            )
            logger.info(f"Initialized LLM: {LLM_MODEL} from {MODEL_PROVIDER}")
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
            for subsection in subsections:
                subsection_name = subsection.get('subsection_name', '')
                if subsection_name.lower() == subsection_type.lower():
                    start_page = subsection.get('start_page')
                    end_page = subsection.get('end_page')
                    
                    if start_page and end_page:
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
                            return self.extract_subsection_pages(start_page, end_page, f"{cluster_name} - {subsection_type}")
            
            logger.warning(f"No {subsection_type} subsection found for {cluster_name}")
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting {subsection_type} subsection text: {e}")
            return ""
    
    def extract_cluster_overview_combined(self, cluster_data: Dict[str, Any], cluster_name: str) -> Optional[Dict[str, Any]]:
        """
        Extract cluster overview (Cluster ID/IDs + Classification) with a single AI call
        Combines page ranges from all overview subsections for optimal extraction
        
        Args:
            cluster_data: Cluster information from matter_clusters_toc.json
            cluster_name: Name of cluster for context
            
        Returns:
            Dict with cluster_ids, classifications, and references or None
        """
        try:
            subsections = cluster_data.get('subsections', [])
            
            # Find all cluster overview subsections and collect their page ranges
            overview_subsections = []
            for subsection in subsections:
                subsection_name = subsection.get('subsection_name', '')
                if subsection_name in ['Cluster ID', 'Cluster IDs', 'Classification']:
                    start_page = subsection.get('start_page')
                    end_page = subsection.get('end_page')
                    if start_page and end_page:
                        overview_subsections.append({
                            'name': subsection_name,
                            'start_page': start_page,
                            'end_page': end_page
                        })
            
            if not overview_subsections:
                logger.warning(f"No cluster overview subsections found for {cluster_name}")
                return None
            
            # Calculate combined page range: min(start) to max(end)
            min_start = min(sub['start_page'] for sub in overview_subsections)
            max_end = max(sub['end_page'] for sub in overview_subsections)
            
            overview_names = [sub['name'] for sub in overview_subsections]
            
            # Extract text from combined page range
            section_text = self.extract_subsection_pages(min_start, max_end, f"{cluster_name} - Cluster Overview")
            
            if not section_text:
                logger.warning(f"Failed to extract cluster overview text for {cluster_name}")
                return None
            
            # Use CLUSTER_OVERVIEW_EXTRACTION_PROMPT
            section_prompt = section_prompt_dict.get('Cluster ID', '')  # All overview types use same prompt
            if not section_prompt:
                logger.error(f"No prompt found for cluster overview")
                return None
            
            # Add section context
            section_context = f"\n\n**SECTION TO EXTRACT FROM:**\nCluster Overview (ID + Classification) from {cluster_name}\n\n**SECTION TEXT:**\n{section_text}"
            final_prompt = section_prompt + section_context
            
            logger.info(f"Making single AI call for cluster overview in {cluster_name} (text length: {len(section_text)})")
            
            # Get LLM response
            response = self.llm.invoke(final_prompt)
            time.sleep(30)
            
            # Clean up response
            response_text = response.content if hasattr(response, 'content') else str(response)
            response_text = re.sub(r'```json\s*', '', response_text)
            response_text = re.sub(r'```\s*', '', response_text)
            response_text = response_text.strip()
            
            # Try to parse JSON response
            try:
                result = json.loads(response_text)
                logger.info(f"✓ Successfully extracted cluster overview for {cluster_name} with single AI call")
                return result
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parsing failed for cluster overview in {cluster_name}: {e}")
                logger.debug(f"Raw response preview: {response_text[:500]}...")
                
                # Try to repair the JSON
                logger.warning(f"Attempting repair for cluster overview in {cluster_name}...")
                repaired_result = self._attempt_json_repair(response_text, "Cluster Overview", cluster_name)
                if repaired_result:
                    logger.info(f"✓ Successfully repaired JSON for cluster overview in {cluster_name}")
                    return repaired_result
                
                logger.error(f"Failed to parse cluster overview response for {cluster_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting cluster overview for {cluster_name}: {e}")
            return None
    
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
            
            # Get LLM response
            response = self.llm.invoke(final_prompt)
            time.sleep(30)
            
            # Clean up response before JSON parsing
            response_text = response.content if hasattr(response, 'content') else str(response)
            response_text = re.sub(r'```json\s*', '', response_text)
            response_text = re.sub(r'```\s*', '', response_text)
            response_text = response_text.strip()
            
            # Check if response looks truncated
            if len(response_text) > 30000 and not response_text.endswith(('}', ']')):
                logger.warning(f"Response for {section_type} in {cluster_name} appears truncated ({len(response_text)} chars)")
            
            # Try to parse JSON response
            try:
                result = json.loads(response_text)
                logger.info(f"Successfully extracted {section_type} for {cluster_name} from direct PDF text")
                return result
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parsing failed for {section_type} in {cluster_name}: {e}")
                logger.debug(f"Raw response preview: {response_text[:500]}...")
                
                # Try to repair the JSON
                logger.warning(f"Attempting repair for {section_type} in {cluster_name}...")
                repaired_result = self._attempt_json_repair(response_text, section_type, cluster_name)
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
        
        logger.info(f"Processing: {cluster_name} ({section_number})")
        
        # Initialize cluster info with cluster_name from TOC
        # This provides the cluster name from matter_clusters_toc.json
        cluster_info = {
            "cluster_name": cluster_name
        }
        
        # Track all references across all sections
        all_references = []
        
        # OPTIMIZATION: Process cluster overview (Cluster ID/IDs + Classification) first with single AI call
        overview_result = self.extract_cluster_overview_combined(cluster_data, cluster_name)
        
        # Dynamic handler for overview result - same as all other subsections
        if overview_result and isinstance(overview_result, dict):
            refs = overview_result.get('references', [])
            if refs:
                all_references.extend(refs)
                overview_result_copy = overview_result.copy()
                overview_result_copy.pop('references', None)
                cluster_info.update(overview_result_copy)
            else:
                cluster_info.update(overview_result)
        
        # Create set of already processed subsections
        processed_subsections = {'Cluster ID', 'Cluster IDs', 'Classification'} if overview_result else set()
        
        # Dynamically extract remaining subsections using section_prompt_dict
        for subsection in subsections:
            subsection_name = subsection.get('subsection_name', '')
            
            # Skip if already processed in cluster overview
            if subsection_name in processed_subsections:
                continue
            
            # Get the appropriate prompt from section_prompt_dict
            if subsection_name not in section_prompt_dict:
                logger.warning(f"No prompt found for subsection '{subsection_name}' in {cluster_name}, skipping")
                continue
            
            section_prompt = section_prompt_dict[subsection_name]
            
            # Extract the subsection data
            result = self.extract_section_with_direct_text(cluster_data, section_prompt, subsection_name, cluster_name)

            if result is None:
                continue
            
            # Dynamic handler for all subsection types - keeps subsection name as-is
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
        
        # Deduplicate references by name
        unique_references = {}
        for ref in all_references:
            ref_name = ref.get('name', '')
            if ref_name and ref_name not in unique_references:
                unique_references[ref_name] = ref
        
        # Add references to cluster_info
        cluster_info['references'] = list(unique_references.values())
        
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
    
    def process_cluster_by_number(self, cluster_number: int):
        """
        Process a single cluster by its index number
        
        Args:
            cluster_number: Cluster index (1-based)
        """
        clusters_list = list(self.clusters_data.get('clusters', {}).items())
        
        if cluster_number < 1 or cluster_number > len(clusters_list):
            logger.error(f"Invalid cluster number: {cluster_number}. Valid range: 1-{len(clusters_list)}")
            return
        
        cluster_key, cluster_data = clusters_list[cluster_number - 1]
        section_number = cluster_data.get('section_number', cluster_key)
        cluster_name = cluster_data.get('cluster_name', 'Unknown')
        
        try:
            logger.info(f"{'='*80}")
            logger.info(f"Processing cluster {cluster_number}: {cluster_name}")
            
            cluster_result = self.process_cluster_enhanced(cluster_data)
            
            if cluster_result is None:
                logger.warning(f"✗ Failed: {cluster_name}")
                return
            
            if self.save_cluster_to_file(cluster_result, cluster_name, section_number):
                logger.info(f"✓ Successfully processed cluster {cluster_number}")
            else:
                logger.warning(f"✗ Failed to save cluster {cluster_number}")
                
        except Exception as e:
            logger.error(f"✗ Error processing cluster {cluster_number}: {e}")
            raise


def main():
    """Main function"""
    pdf_path = os.path.join("..", "Matter-1.4-Application-Cluster-Specification.pdf")
    clusters_json_path = "matter_clusters_toc.json"
    output_dir = "cluster_details"
    
    # Check files exist
    if not os.path.exists(clusters_json_path):
        logger.error(f"Clusters JSON file not found: {clusters_json_path}")
        return
    
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return
    
    try:
        extractor = EnhancedClusterExtractor(pdf_path, clusters_json_path, output_dir)
        
        # Process specific cluster by number (1-based index)
        extractor.process_cluster_by_number(cluster_number=5)
        
    except KeyboardInterrupt:
        logger.warning("Extraction interrupted by user")
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        
if __name__ == "__main__":
    main()