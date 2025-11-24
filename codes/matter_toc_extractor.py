#!/usr/bin/env python3
"""
Manual Matter PDF Table of Contents Extractor
Extracts cluster information with subsections directly from PDF
Pure manual parsing - no AI or RAG components
"""

import os
import json
import logging
import re
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

# Configuration
from config import *

# PDF imports
import fitz  # PyMuPDF

@dataclass
class SubsectionInfo:
    """Subsection information extracted from TOC"""
    subsection_name: str
    subsection_number: str
    start_page: int
    end_page: Optional[int]

@dataclass
class ClusterInfo:
    """Cluster information extracted from TOC"""
    cluster_name: str
    section_number: str
    start_page: int
    end_page: Optional[int]
    category: str = ""
    subsections: List[SubsectionInfo] = None
    
    def __post_init__(self):
        if self.subsections is None:
            self.subsections = []

class ManualTOCExtractor:
    """
    Manual TOC extractor for Matter PDF specification
    Extracts TOC directly from PDF without AI/RAG
    """
    
    def __init__(self, pdf_path: str = None):
        self.pdf_path = pdf_path or PDF_PATH
        self.extracted_clusters = {}
        self.toc_content = ""
        self.total_pdf_pages = 0
        
        # Setup logging
        logging.basicConfig(level=getattr(logging, LOG_LEVEL))
        self.logger = logging.getLogger(__name__)
        
    def extract_toc_from_pdf(self) -> str:
        """Extract table of contents from PDF"""
        try:
            doc = fitz.open(self.pdf_path)
            self.total_pdf_pages = len(doc)
            
            toc_content = ""
            
            # Get TOC from PDF metadata if available
            toc = doc.get_toc()
            if toc:
                for level, title, page in toc:
                    indent = "  " * (level - 1)
                    toc_content += f"{indent}{title} ... {page}\n"
            else:
                toc_content = self._extract_toc_from_text(doc)
            
            doc.close()
            self.toc_content = toc_content
            
            # Save raw TOC for debugging
            toc_file = os.path.join(OUTPUT_DIRECTORY, RAW_TOC_FILE)
            with open(toc_file, 'w', encoding='utf-8') as f:
                f.write(toc_content)
            
            self.logger.info(f"TOC extracted and saved to: {toc_file}")
            return toc_content
            
        except Exception as e:
            self.logger.error(f"Error extracting TOC: {e}")
            raise
    
    def _extract_toc_from_text(self, doc) -> str:
        """Extract TOC from PDF text content"""
        toc_content = ""
        
        # Look for TOC in first 50 pages (as configured)
        for page_num in range(min(MAX_TOC_PAGES, len(doc))):
            page = doc.load_page(page_num)
            text = page.get_text()
            
            # Look for TOC patterns
            if self._is_toc_page(text):
                toc_content += f"\n--- Page {page_num + 1} ---\n"
                toc_content += text
        
        return toc_content
    
    def _is_toc_page(self, text: str) -> bool:
        """Check if page contains TOC content"""
        text_lower = text.lower()
        for indicator in TOC_INDICATORS:
            if indicator in text_lower or re.search(indicator, text, re.IGNORECASE):
                return True
        
        return False
    
    def extract_clusters_from_toc(self) -> Dict[str, ClusterInfo]:
        """Extract clusters and subsections from TOC content"""
        if not self.toc_content:
            self.extract_toc_from_pdf()
        
        if not self.toc_content:
            self.logger.error("Failed to extract TOC content")
            return {}
        
        toc_lines = self.toc_content.split('\n')
        
        clusters = {}
        current_cluster = None
        
        for line in toc_lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for cluster (2-level numbering with "Cluster" or "Clusters" in name)
            cluster_match = re.match(r'(\d+\.\d+)\.\s+(.+Clusters?)\s+\.\.\.\s+(\d+)', line)
            if cluster_match:
                # Save previous cluster if exists
                if current_cluster:
                    clusters[current_cluster.section_number] = current_cluster
                
                section_num = cluster_match.group(1)
                cluster_name = cluster_match.group(2)
                start_page = int(cluster_match.group(3))
                
                # Determine category
                section_prefix = int(section_num.split('.')[0])
                category = self._get_category(section_prefix)
                
                current_cluster = ClusterInfo(
                    cluster_name=cluster_name,
                    section_number=section_num,
                    start_page=start_page,
                    end_page=None,  # Will be calculated later
                    category=category,
                    subsections=[]
                )
                continue
            
            # Check for subsection (3-level numbering under current cluster)
            if current_cluster:
                subsection_match = re.match(r'(\d+\.\d+\.\d+)\.\s+(.+?)\s+\.\.\.\s+(\d+)', line)
                if subsection_match:
                    subsection_num = subsection_match.group(1)
                    subsection_name = subsection_match.group(2)
                    start_page = int(subsection_match.group(3))
                    
                    # Check if this subsection belongs to current cluster
                    if subsection_num.startswith(current_cluster.section_number + '.'):
                        subsection = SubsectionInfo(
                            subsection_name=subsection_name,
                            subsection_number=subsection_num,
                            start_page=start_page,
                            end_page=None  # Will be calculated later
                        )
                        current_cluster.subsections.append(subsection)
        
        # Don't forget the last cluster
        if current_cluster:
            clusters[current_cluster.section_number] = current_cluster
        
        # Calculate end pages
        self._calculate_end_pages(clusters)
        
        self.extracted_clusters = clusters
        return clusters
    
    def _get_category(self, section_prefix: int) -> str:
        """Get category based on section number"""
        categories = {
            1: "General",
            2: "Measurement and Sensing", 
            3: "Lighting",
            4: "HVAC",
            5: "Closures",
            6: "Media",
            7: "Robots",
            8: "Home Appliances",
            9: "Energy Management",
            10: "Network Infrastructure"
        }
        return categories.get(section_prefix, "Unknown")
    
    def _calculate_end_pages(self, clusters: Dict[str, ClusterInfo]):
        """Calculate end pages for clusters and subsections using proper logic"""
        cluster_list = list(clusters.values())
        cluster_list.sort(key=lambda x: (int(x.section_number.split('.')[0]), int(x.section_number.split('.')[1])))
        
        # First, calculate cluster end pages (cluster to cluster)
        for i, cluster in enumerate(cluster_list):
            if i < len(cluster_list) - 1:
                # Cluster end page = next cluster's start page
                next_cluster = cluster_list[i + 1]
                cluster.end_page = next_cluster.start_page
            else:
                # Last cluster = total PDF pages
                cluster.end_page = self.total_pdf_pages
        
        # Second, calculate subsection end pages within each cluster
        for cluster in cluster_list:
            if cluster.subsections:
                # Sort subsections by section number
                cluster.subsections.sort(key=lambda x: [int(n) for n in x.subsection_number.split('.')])
                
                for j, subsection in enumerate(cluster.subsections):
                    if j < len(cluster.subsections) - 1:
                        # Subsection end page = next subsection's start page
                        next_subsection = cluster.subsections[j + 1]
                        subsection.end_page = next_subsection.start_page
                    else:
                        # Last subsection in cluster = cluster's end page
                        subsection.end_page = cluster.end_page
    
    def save_clusters_to_json(self, output_file: str = None):
        """Save extracted clusters to JSON file"""
        if not self.extracted_clusters:
            self.logger.error("No clusters extracted. Run extraction method first.")
            return
        
        output_file = output_file or OUTPUT_JSON_FILE
        output_path = os.path.join(OUTPUT_DIRECTORY, output_file)
        
        # Convert to serializable format
        clusters_data = {}
        for section, cluster in self.extracted_clusters.items():
            cluster_dict = asdict(cluster)
            # Convert subsections to dict format
            if cluster_dict.get('subsections'):
                cluster_dict['subsections'] = [asdict(sub) for sub in cluster.subsections]
            clusters_data[section] = cluster_dict
        
        # Collect all unique subsection names
        all_subsection_names = set()
        subsection_counts = {}
        
        for cluster in clusters_data.values():
            for subsection in cluster.get("subsections", []):
                subsection_name = subsection.get("subsection_name", "")
                if subsection_name:
                    all_subsection_names.add(subsection_name)
                    subsection_counts[subsection_name] = subsection_counts.get(subsection_name, 0) + 1
        
        # Sort subsections by frequency (most common first)
        sorted_subsections = sorted(all_subsection_names, 
                                  key=lambda x: subsection_counts[x], 
                                  reverse=True)
        
        # Create final JSON structure
        final_data = {
            "metadata": {
                "total_clusters": len(clusters_data),
                "categories": list(set(cluster["category"] for cluster in clusters_data.values())),
                "extraction_method": "Manual parsing from PDF",
                "source_pdf": os.path.basename(self.pdf_path),
                "total_pdf_pages": self.total_pdf_pages,
                "includes_subsections": True,
                "total_unique_subsections": len(all_subsection_names),
                "all_subsection_types": sorted_subsections,
                "subsection_frequency": subsection_counts
            },
            "clusters": clusters_data
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Clusters saved to: {output_path}")
        return output_path
    
    def print_clusters_summary(self):
        """Print summary of extracted clusters"""
        if not self.extracted_clusters:
            print("No clusters extracted yet.")
            return
        
        print(f"\n🔍 Extracted {len(self.extracted_clusters)} Matter Clusters")
        print("=" * 70)
        
        # Group by category
        categories = {}
        for cluster in self.extracted_clusters.values():
            if cluster.category not in categories:
                categories[cluster.category] = []
            categories[cluster.category].append(cluster)
        
        for category, clusters in categories.items():
            print(f"\n📂 {category} ({len(clusters)} clusters):")
            for cluster in sorted(clusters, key=lambda x: x.section_number):
                print(f"   {cluster.section_number}. {cluster.cluster_name}")
                end_page_str = str(cluster.end_page) if cluster.end_page is not None else "end"
                print(f"      Pages: {cluster.start_page}-{end_page_str}")
                if cluster.subsections:
                    print(f"      Subsections ({len(cluster.subsections)}):")
                    for subsection in cluster.subsections:
                        sub_end_str = str(subsection.end_page) if subsection.end_page is not None else "end"
                        print(f"        {subsection.subsection_number}. {subsection.subsection_name} (p.{subsection.start_page}-{sub_end_str})")


def main():
    """Main function for manual TOC extraction"""
    print("🚀 Matter PDF Table of Contents Extractor (Manual)")
    print("=" * 50)
    
    try:
        # Create extractor
        extractor = ManualTOCExtractor()
        
        # Extract TOC from PDF first
        print("\n🔍 Step 1: Extracting TOC from PDF...")
        toc_content = extractor.extract_toc_from_pdf()
        
        if not toc_content:
            print("❌ No TOC content found")
            return
        
        # Extract clusters and subsections
        print("\n� Step 2: Parsing clusters from TOC...")
        clusters = extractor.extract_clusters_from_toc()
        
        if not clusters:
            print("❌ No clusters found")
            return
        
        # Save results
        print("\n💾 Saving results...")
        json_file = extractor.save_clusters_to_json()
        
        # Display summary
        extractor.print_clusters_summary()
        
        print(f"\n✅ Extraction completed successfully!")
        print(f"📄 Results saved to: {json_file}")
        print(f"📊 Total clusters: {len(clusters)}")
        print(f"🔧 Method: Manual parsing")
        
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        logging.error(f"Extraction failed: {e}", exc_info=True)


if __name__ == "__main__":
    main()