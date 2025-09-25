#!/usr/bin/env python3
"""
Enhanced Matter Cluster Detail Extractor with Section-Based Approach
Follows existing RAG pattern but uses targeted section extraction for higher accuracy
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
from langchain_google_genai import GoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from config import (
    GOOGLE_API_KEY, GEMINI_MODEL, GEMINI_TEMPERATURE, GEMINI_MAX_OUTPUT_TOKENS,
    CLUSTER_PAGE_BUFFER, PDF_PAGE_OFFSET, EMBEDDINGS_MODEL, CHUNK_SIZE, CHUNK_OVERLAP, VECTOR_SEARCH_K,
    REVISION_HISTORY_EXTRACTION_PROMPT, FEATURES_EXTRACTION_PROMPT, DATA_TYPES_EXTRACTION_PROMPT,
    ATTRIBUTES_EXTRACTION_PROMPT, COMMANDS_EXTRACTION_PROMPT, EVENTS_EXTRACTION_PROMPT
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
        
        # Section patterns for identifying cluster sections
        self.section_patterns = {
            'revision_history': [
                r'(\d+\.\d+\.1\.?\s*Revision\s+History)',
                r'(\d+\.\d+\.1\.?\s*revision\s+history)',
                r'(Revision\s+History)',
                r'(revision\s+history)'
            ],
            'classification': [
                r'(\d+\.\d+\.2\.?\s*Classification)',
                r'(\d+\.\d+\.2\.?\s*classification)',
                r'(Classification)'
            ],
            'cluster_id': [
                r'(\d+\.\d+\.3\.?\s*Cluster\s+ID)',
                r'(\d+\.\d+\.3\.?\s*cluster\s+id)',
                r'(Cluster\s+ID)'
            ],
            'features': [
                r'(\d+\.\d+\.3\.?\d*\s*Features?)',
                r'(\d+\.\d+\.3\.?\d*\s*features?)',
                r'(Features?)'
            ],
            'data_types': [
                r'(\d+\.\d+\.[4-5]\.?\d*\s*Data\s+Types?)',
                r'(\d+\.\d+\.[4-5]\.?\d*\s*data\s+types?)',
                r'(Data\s+Types?)',
                r'(\d+\.\d+\.[4-5]\.?\d*\.?\d*\s*\w+\s*Type)',
                r'(\d+\.\d+\.[4-5]\.?\d*\.?\d*\s*\w+\s*Enum\s*Type)',
                r'(\d+\.\d+\.[4-5]\.?\d*\.?\d*\s*\w+\s*Bitmap\s*Type)',
                r'(\d+\.\d+\.[4-5]\.?\d*\.?\d*\s*\w+\s*Struct\s*Type)'
            ],
            'attributes': [
                r'(\d+\.\d+\.6\.?\d*\s*Attributes?)',
                r'(\d+\.\d+\.6\.?\d*\s*attributes?)',
                r'(Attributes?)'
            ],
            'commands': [
                r'(\d+\.\d+\.7\.?\d*\s*Commands?)',
                r'(\d+\.\d+\.7\.?\d*\s*commands?)',
                r'(Commands?)'
            ],
            'events': [
                r'(\d+\.\d+\.8\.?\d*\s*Events?)',
                r'(\d+\.\d+\.8\.?\d*\s*events?)',
                r'(Events?)'
            ]
        }
        
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
                temperature=GEMINI_TEMPERATURE,
                max_output_tokens=GEMINI_MAX_OUTPUT_TOKENS
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
    
    def extract_cluster_pages(self, start_page: int, end_page: int) -> str:
        """
        Extract text content from PDF pages for a specific cluster
        
        Args:
            start_page: Starting page number (1-indexed)
            end_page: Ending page number (1-indexed)
            
        Returns:
            Extracted text content
        """
        try:
            # Add buffer pages and convert to 0-indexed for PyMuPDF
            actual_start = max(0, start_page - 1 - CLUSTER_PAGE_BUFFER)
            actual_end = min(len(self.pdf_doc), end_page + CLUSTER_PAGE_BUFFER)
            
            text_content = ""
            for page_num in range(actual_start, actual_end):
                page = self.pdf_doc.load_page(page_num)
                text_content += page.get_text()
                text_content += "\n\n"
            
            logger.info(f"Extracted {len(text_content)} characters from pages {actual_start+1}-{actual_end}")
            return text_content
            
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
            # Split text into chunks (same as original approach)
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=CHUNK_SIZE,
                chunk_overlap=CHUNK_OVERLAP,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
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
    
    def extract_section_text_by_number(self, cluster_text: str, section_patterns: List[str], cluster_name: str = "") -> str:
        """
        Extract section text by identifying section numbers in the cluster text
        
        Args:
            cluster_text: Full cluster text content
            section_patterns: List of regex patterns to identify section starts
            cluster_name: Name of cluster for logging
            
        Returns:
            Extracted section text
        """
        try:
            section_text = ""
            
            for pattern in section_patterns:
                matches = list(re.finditer(pattern, cluster_text, re.IGNORECASE | re.MULTILINE))
                
                for match in matches:
                    start_pos = match.start()
                    
                    # Find the end of this section (start of next section or end of text)
                    end_pos = len(cluster_text)
                    
                    # Look for next section header to determine end
                    remaining_text = cluster_text[start_pos + len(match.group()):]
                    next_section_pattern = r'\n\s*\d+\.\d+\.(\d+\.?)*\s+[A-Z]'
                    next_match = re.search(next_section_pattern, remaining_text)
                    if next_match:
                        end_pos = start_pos + len(match.group()) + next_match.start()
                    
                    current_section = cluster_text[start_pos:end_pos].strip()
                    if current_section and len(current_section) > 50:  # Minimum section length
                        section_text += current_section + "\n\n"
                        logger.debug(f"Extracted section text: {current_section[:100]}...")
            
            if section_text:
                logger.info(f"Successfully extracted section text for {cluster_name} (length: {len(section_text)})")
            else:
                logger.warning(f"No section text found for {cluster_name}")
            
            return section_text.strip()
            
        except Exception as e:
            logger.error(f"Error extracting section text for {cluster_name}: {e}")
            return ""
    
    def extract_section_with_rag(self, vector_store: FAISS, section_prompt: str, section_type: str, cluster_name: str = "", cluster_text: str = "") -> Optional[Any]:
        """
        Extract section information using section text approach with specialized prompt
        
        Args:
            vector_store: FAISS vector store (kept for compatibility, not used)
            section_prompt: Specialized prompt for this section type
            section_type: Type of section being extracted
            cluster_name: Name of cluster for context
            cluster_text: Full cluster text to extract section from
            
        Returns:
            Extracted section information
        """
        try:
            if vector_store:
                # RAG approach (commented out as requested)
                section_queries = {
                    'revision_history': "revision history changes versions ClusterRevision",
                    'features': "features bit code capabilities GroupNames",
                    'data_types': "data types enum bitmap struct IdentifyTypeEnum",
                    'attributes': "attributes ID name type constraint quality default access",
                    'commands': "commands ID name direction response effect on receipt",
                    'events': "events ID name priority access conformance"
                }
                
                query = section_queries.get(section_type, f"{section_type} cluster specification")
                docs = vector_store.similarity_search(query, k=VECTOR_SEARCH_K)
                context = "\n\n".join([doc.page_content for doc in docs])
            else:
                # Section text extraction approach (new method)
                section_patterns = self.section_patterns.get(section_type, [])
                context = self.extract_section_text_by_number(cluster_text, section_patterns, cluster_name)
                
                if not context:
                    logger.warning(f"No {section_type} section found for {cluster_name}")
                    return None
            
            # Combine prompt with context
            full_prompt = f"{section_prompt}\n\nSECTION TEXT:\n{context}"
            
            logger.info(f"Extracting {section_type} for {cluster_name} (context length: {len(context)})")
            
            response = self.llm.invoke(full_prompt)
            
            # Attempt to parse JSON response
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                # Try to repair JSON
                return self._attempt_json_repair(response, section_type, cluster_name)
                
        except Exception as e:
            logger.error(f"Error extracting {section_type} for {cluster_name}: {e}")
            return None
    
    def _attempt_json_repair(self, response: str, section_type: str, cluster_name: str) -> Optional[Any]:
        """
        Attempt to repair malformed JSON response (same as original)
        
        Args:
            response: Raw LLM response
            section_type: Type of section being extracted
            cluster_name: Name of cluster for logging
            
        Returns:
            Parsed JSON if repair successful, None otherwise
        """
        try:
            # Remove markdown code blocks
            response = re.sub(r'```json\s*', '', response)
            response = re.sub(r'```\s*', '', response)
            
            # Try to find JSON content
            json_match = re.search(r'[\[\{].*[\]\}]', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            
            logger.warning(f"Could not repair JSON for {section_type} in {cluster_name}")
            return None
            
        except Exception as e:
            logger.error(f"JSON repair failed for {section_type} in {cluster_name}: {e}")
            return None
    
    def identify_sections(self, cluster_text: str, cluster_name: str = "") -> Dict[str, List[Tuple[str, int, int]]]:
        """
        Identify different sections within the cluster text
        
        Args:
            cluster_text: Full cluster text content
            cluster_name: Name of the cluster for context
            
        Returns:
            Dictionary mapping section types to list of (section_text, start_pos, end_pos) tuples
        """
        sections = {}
        
        for section_type, patterns in self.section_patterns.items():
            sections[section_type] = []
            
            for pattern in patterns:
                matches = re.finditer(pattern, cluster_text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    start_pos = match.start()
                    
                    # Find the end of this section (start of next section or end of text)
                    end_pos = len(cluster_text)
                    
                    # Look for next section header to determine end
                    remaining_text = cluster_text[start_pos + len(match.group()):]
                    next_section_pattern = r'\n\s*\d+\.\d+\.\d+'
                    next_match = re.search(next_section_pattern, remaining_text)
                    if next_match:
                        end_pos = start_pos + len(match.group()) + next_match.start()
                    
                    section_text = cluster_text[start_pos:end_pos].strip()
                    if section_text and len(section_text) > 50:  # Minimum section length
                        sections[section_type].append((section_text, start_pos, end_pos))
                        logger.debug(f"Found {section_type} section: {section_text[:100]}...")
        
        logger.info(f"Identified sections for {cluster_name}: {[f'{k}({len(v)})' for k, v in sections.items() if v]}")
        return sections
    
    def get_cluster_id_from_text(self, cluster_text: str) -> str:
        """Extract cluster ID from text"""
        # Look for hex patterns like 0x0003
        id_match = re.search(r'0x[0-9A-Fa-f]{4}', cluster_text)
        if id_match:
            return id_match.group(0)
        return "Unknown"
    
    def get_classification_from_text(self, cluster_text: str) -> Dict[str, str]:
        """Extract classification info from text"""
        import re
        classification = {
            "hierarchy": "Unknown",
            "role": "Unknown", 
            "scope": "Unknown",
            "pics_code": "Unknown"
        }
        
        # Look for classification table patterns
        classification_match = re.search(r'Classification.*?Hierarchy\s*Role\s*Scope\s*PICS\s*Code\s*(\w+)\s*(\w+)\s*(\w+)\s*(\w+)', 
                                        cluster_text, re.IGNORECASE | re.DOTALL)
        if classification_match:
            classification["hierarchy"] = classification_match.group(1)
            classification["role"] = classification_match.group(2)
            classification["scope"] = classification_match.group(3)
            classification["pics_code"] = classification_match.group(4)
        
        return classification
    
    def save_cluster_sections(self, cluster_text: str, cluster_name: str) -> Dict[str, str]:
        """
        Save section texts at the start of cluster extraction for reference
        
        Args:
            cluster_text: Full cluster text content
            cluster_name: Name of cluster for logging
            
        Returns:
            Dictionary mapping section types to their extracted text
        """
        cluster_sections = {}
        
        for section_type, patterns in self.section_patterns.items():
            section_text = self.extract_section_text_by_number(cluster_text, patterns, cluster_name)
            if section_text:
                cluster_sections[section_type] = section_text
                logger.debug(f"Saved {section_type} section for {cluster_name}: {len(section_text)} chars")
        
        logger.info(f"Saved {len(cluster_sections)} sections for {cluster_name}")
        return cluster_sections

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
        
        logger.info(f"Processing cluster: {cluster_name} ({section_number}) pages {start_page}-{end_page}")
        
        # Extract full cluster text (same as original)
        cluster_text = self.extract_cluster_pages(start_page, end_page)
        if not cluster_text:
            logger.error(f"Failed to extract text for {cluster_name}")
            return self._create_fallback_cluster_info(cluster_name, section_number, category)
        
        # Save section texts at the start of cluster extraction
        cluster_sections = self.save_cluster_sections(cluster_text, cluster_name)
        
        # Create vector store (same as original RAG approach)
        # vector_store = self.create_vector_store(cluster_text)
        # if not vector_store:
        #     logger.error(f"Failed to create vector store for {cluster_name}")
        #     return self._create_fallback_cluster_info(cluster_name, section_number, category)
        vector_store = None
        
        # Extract basic info
        cluster_id = self.get_cluster_id_from_text(cluster_text)
        classification = self.get_classification_from_text(cluster_text)
        
        # Extract each section using specialized prompts with section text
        revision_history = []
        result = self.extract_section_with_rag(vector_store, REVISION_HISTORY_EXTRACTION_PROMPT, 'revision_history', cluster_name, cluster_text)
        if result and isinstance(result, list):
            revision_history = result
        
        features = []
        result = self.extract_section_with_rag(vector_store, FEATURES_EXTRACTION_PROMPT, 'features', cluster_name, cluster_text)
        if result and isinstance(result, list):
            features = result
        
        data_types = []
        result = self.extract_section_with_rag(vector_store, DATA_TYPES_EXTRACTION_PROMPT, 'data_types', cluster_name, cluster_text)
        if result and isinstance(result, list):
            data_types = result
        
        attributes = []
        result = self.extract_section_with_rag(vector_store, ATTRIBUTES_EXTRACTION_PROMPT, 'attributes', cluster_name, cluster_text)
        if result and isinstance(result, list):
            attributes = result
        
        commands = []
        result = self.extract_section_with_rag(vector_store, COMMANDS_EXTRACTION_PROMPT, 'commands', cluster_name, cluster_text)
        if result and isinstance(result, list):
            commands = result
        
        events = []
        result = self.extract_section_with_rag(vector_store, EVENTS_EXTRACTION_PROMPT, 'events', cluster_name, cluster_text)
        if result and isinstance(result, list):
            events = result
        
        # Build final cluster info structure (EXACT same structure as original)
        cluster_info = {
            "cluster_name": cluster_name,
            "cluster_id": cluster_id,
            "classification": classification,
            "revision_history": revision_history,
            "features": features,
            "data_types": data_types,
            "attributes": attributes,
            "commands": commands,
            "events": events,
            "global_attributes": []
        }
        
        return {
            "cluster_info": cluster_info,
            "metadata": {
                "source_pages": f"{start_page}-{end_page}",
                "extraction_method": "enhanced_section_based",
                "text_length": len(cluster_text),
                "section_number": section_number,
                "category": category
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
{full_cluster_text[:8000]}...

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
    
    def _create_fallback_cluster_info(self, cluster_name: str, section_number: str, category: str) -> Dict[str, Any]:
        """Create fallback cluster info when extraction fails (same as original)"""
        return {
            "cluster_info": {
                "cluster_name": cluster_name,
                "cluster_id": "Unknown",
                "classification": {
                    "hierarchy": "Unknown",
                    "role": "Unknown",
                    "scope": "Unknown", 
                    "pics_code": "Unknown"
                },
                "revision_history": [],
                "features": [],
                "data_types": [],
                "attributes": [],
                "commands": [],
                "events": [],
                "global_attributes": []
            },
            "metadata": {
                "source_pages": "Unknown",
                "extraction_method": "fallback",
                "text_length": 0,
                "section_number": section_number,
                "category": category,
                "error": "Failed to extract cluster text"
            }
        }
    
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
                
                # Extract full cluster text for final validation
                start_page = cluster_data.get('start_page', 1)
                end_page = cluster_data.get('end_page', 1)
                full_cluster_text = self.extract_cluster_pages(start_page, end_page)
                
                # Final validation and enhancement step
                if full_cluster_text:
                    cluster_result = self.validate_and_enhance_cluster(cluster_result, full_cluster_text)
                
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
                # Add fallback entry
                fallback_result = self._create_fallback_cluster_info(
                    cluster_data.get('cluster_name', 'Unknown'),
                    section_number,
                    cluster_data.get('category', 'Unknown')
                )
                results['clusters'].append(fallback_result)
                processed_count += 1
        
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
        results = extractor.process_all_clusters(limit=3, resume=True)
        
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