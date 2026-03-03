"""
Retrieve previously processed PDF result from Datalab.to Marker API.

Usage:
    python retrieve_datalab_result.py

Requirements:
    pip install requests
"""

import requests
from pathlib import Path
import json
import base64


# ── Configuration ──────────────────────────────────────────────────────
DATALAB_API_KEY = "c1ejCynW6sr8snAa5S3YyJIJ2td4NZVzKBCB6y5Rtd8"
REQUEST_ID = "B9qOQmTgJttmmvZql_uoRA"
OUTPUT_DIR = Path("./application_spec")

# API endpoint
BASE_URL = "https://www.datalab.to/api/v1"


def retrieve_result(api_key: str, request_id: str, output_dir: Path) -> None:
    """
    Retrieve result from Datalab Marker API and save to files.
    
    Args:
        api_key: Your Datalab API key
        request_id: The request ID from playground URL
        output_dir: Directory to save output files
    """
    # Create output directory
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Build URL and headers
    url = f"{BASE_URL}/marker/{request_id}"
    headers = {"X-API-Key": api_key}
    
    print(f"🔗 Connecting to Datalab API...")
    print(f"📥 Retrieving request: {request_id}")
    print(f"   URL: {url}")
    
    try:
        # Make GET request to retrieve result
        response = requests.get(url, headers=headers, timeout=30)
        
        # Check HTTP status
        if response.status_code == 404:
            print(f"❌ Request not found (404)")
            print(f"   The request ID '{request_id}' doesn't exist or has expired.")
            print(f"   Results are deleted 1 hour after processing completes.")
            return
        elif response.status_code == 401:
            print(f"❌ Authentication failed (401)")
            print(f"   Your API key may be invalid or expired.")
            return
        elif response.status_code != 200:
            print(f"❌ HTTP {response.status_code}: {response.text[:500]}")
            return
        
        # Parse JSON response
        result = response.json()
        
        print(f"✅ Status: {result.get('status', 'unknown')}")
        
        status = result.get('status')
        
        if status == "complete":
            success = result.get('success', False)
            if not success:
                print(f"❌ Processing completed but was not successful")
                print(f"   Error: {result.get('error', 'Unknown error')}")
                return
            
            # Save markdown
            if 'markdown' in result and result['markdown']:
                md_path = output_dir / "output.md"
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(result['markdown'])
                size_kb = md_path.stat().st_size / 1024
                print(f"📝 Saved markdown: {md_path} ({size_kb:.1f} KB)")
            
            # Save HTML
            if 'html' in result and result['html']:
                html_path = output_dir / "output.html"
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(result['html'])
                size_kb = html_path.stat().st_size / 1024
                print(f"🌐 Saved HTML: {html_path} ({size_kb:.1f} KB)")
            
            # Save JSON
            if 'json' in result and result['json']:
                json_path = output_dir / "output_structured.json"
                with open(json_path, 'w', encoding='utf-8') as f:
                    if isinstance(result['json'], str):
                        f.write(result['json'])
                    else:
                        json.dump(result['json'], f, indent=2, ensure_ascii=False)
                size_kb = json_path.stat().st_size / 1024
                print(f"📊 Saved structured JSON: {json_path} ({size_kb:.1f} KB)")
            
            # Save images (base64 encoded)
            if 'images' in result and result['images']:
                img_dir = output_dir / "images"
                img_dir.mkdir(exist_ok=True)
                img_count = 0
                for img_name, img_b64 in result['images'].items():
                    img_path = img_dir / img_name
                    # Decode base64 to bytes
                    img_bytes = base64.b64decode(img_b64)
                    with open(img_path, 'wb') as f:
                        f.write(img_bytes)
                    img_count += 1
                print(f"🖼️  Saved {img_count} images to: {img_dir}")
            
            # Save full result metadata
            metadata = {
                "request_id": request_id,
                "status": result.get('status'),
                "success": result.get('success'),
                "page_count": result.get('page_count'),
                "parse_quality_score": result.get('parse_quality_score'),
                "cost_breakdown": result.get('cost_breakdown'),
                "metadata": result.get('metadata'),
            }
            meta_path = output_dir / "metadata.json"
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)
            print(f"ℹ️  Saved metadata: {meta_path}")
            
            # Print quality score if available
            if 'parse_quality_score' in result and result['parse_quality_score'] is not None:
                score = result['parse_quality_score']
                print(f"📊 Parse Quality Score: {score:.2f}/5.0")
            
            print(f"\n✨ All files saved to: {output_dir.absolute()}")
            
        elif status == "processing":
            print("⏳ Document is still being processed. Try again in a few moments.")
            print("   Tip: Use the polling script to wait automatically.")
        elif status == "failed":
            print(f"❌ Processing failed.")
            print(f"   Error: {result.get('error', 'Unknown error')}")
        else:
            print(f"⚠️  Unknown status: {status}")
            print(f"   Full response: {json.dumps(result, indent=2)[:500]}")
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: Cannot reach datalab.to")
        print(f"   Check your internet connection or firewall settings.")
        print(f"   Error: {e}")
    except requests.exceptions.Timeout:
        print(f"❌ Request timeout: Server took too long to respond.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON response from server")
        print(f"   Response text: {response.text[:500]}")
    except Exception as e:
        print(f"❌ Error retrieving result: {e}")
        print(f"\n💡 Troubleshooting:")
        print(f"   1. Verify your API key is correct (get from datalab.to/settings)")
        print(f"   2. Check the request ID format (from playground URL)")
        print(f"   3. Ensure the request exists and hasn't expired (1-hour limit)")
        raise


if __name__ == "__main__":
    print("=" * 70)
    print("  Datalab.to Marker API - Result Retrieval")
    print("=" * 70)
    print()
    
    retrieve_result(DATALAB_API_KEY, REQUEST_ID, OUTPUT_DIR)
