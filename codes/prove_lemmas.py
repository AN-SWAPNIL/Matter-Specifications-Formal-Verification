#!/usr/bin/env python3
"""
Tamarin Lemma Prover - Extracts and proves lemmas individually
"""

import subprocess
import re
import json
from pathlib import Path
from datetime import datetime

def extract_lemmas(spthy_file):
    """Extract all lemma names from a Tamarin file"""
    lemmas = []
    with open(spthy_file, 'r') as f:
        content = f.read()
    
    # Regex to match lemma declarations
    # Matches: lemma name: or lemma name [attributes]:
    pattern = r'lemma\s+(\w+)(?:\s*\[[\w\s,=]*\])?\s*:'
    matches = re.finditer(pattern, content)
    
    for match in matches:
        lemmas.append(match.group(1))
    
    return lemmas

def prove_lemma(spthy_file, lemma_name, timeout=300):
    """
    Prove a single lemma using Tamarin
    
    Args:
        spthy_file: Path to .spthy file
        lemma_name: Name of lemma to prove
        timeout: Timeout in seconds (default 5 minutes)
    
    Returns:
        dict with result info
    """
    cmd = [
        'tamarin-prover',
        '--prove',
        f'--lemma={lemma_name}',
        str(spthy_file)
    ]
    
    print(f"\n{'='*70}")
    print(f"Proving: {lemma_name}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*70}")
    
    start_time = datetime.now()
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        output = result.stdout + result.stderr
        
        # Parse result
        if 'verified' in output.lower():
            status = 'VERIFIED'
        elif 'falsified' in output.lower():
            status = 'FALSIFIED'
        elif 'analysis incomplete' in output.lower():
            status = 'INCOMPLETE'
        else:
            status = 'UNKNOWN'
        
        return {
            'lemma': lemma_name,
            'status': status,
            'time': elapsed,
            'output': output,
            'returncode': result.returncode
        }
        
    except subprocess.TimeoutExpired:
        elapsed = timeout
        return {
            'lemma': lemma_name,
            'status': 'TIMEOUT',
            'time': elapsed,
            'output': f'Timeout after {timeout}s',
            'returncode': -1
        }
    except Exception as e:
        return {
            'lemma': lemma_name,
            'status': 'ERROR',
            'time': 0,
            'output': str(e),
            'returncode': -1
        }

def prove_all_lemmas(spthy_file, timeout_per_lemma=300, output_json=None):
    """
    Extract and prove all lemmas from a Tamarin file
    
    Args:
        spthy_file: Path to .spthy file
        timeout_per_lemma: Timeout per lemma in seconds
        output_json: Optional path to save results as JSON
    """
    spthy_path = Path(spthy_file)
    
    if not spthy_path.exists():
        print(f"Error: File not found: {spthy_file}")
        return
    
    print(f"\nExtracting lemmas from: {spthy_file}")
    lemmas = extract_lemmas(spthy_file)
    
    print(f"Found {len(lemmas)} lemmas:")
    for i, lemma in enumerate(lemmas, 1):
        print(f"  {i}. {lemma}")
    
    if not lemmas:
        print("No lemmas found!")
        return
    
    # Prove each lemma
    results = []
    for i, lemma in enumerate(lemmas, 1):
        print(f"\n[{i}/{len(lemmas)}] Proving {lemma}...")
        result = prove_lemma(spthy_file, lemma, timeout_per_lemma)
        results.append(result)
        
        # Print summary
        status_color = {
            'VERIFIED': '✓',
            'FALSIFIED': '✗',
            'INCOMPLETE': '⚠',
            'TIMEOUT': '⏱',
            'UNKNOWN': '?',
            'ERROR': '⚠'
        }
        symbol = status_color.get(result['status'], '?')
        print(f"{symbol} {result['status']} ({result['time']:.2f}s)")
    
    # Print summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    
    verified = sum(1 for r in results if r['status'] == 'VERIFIED')
    falsified = sum(1 for r in results if r['status'] == 'FALSIFIED')
    incomplete = sum(1 for r in results if r['status'] == 'INCOMPLETE')
    timeout = sum(1 for r in results if r['status'] == 'TIMEOUT')
    error = sum(1 for r in results if r['status'] in ['UNKNOWN', 'ERROR'])
    
    print(f"Total lemmas:     {len(results)}")
    print(f"✓ Verified:       {verified}")
    print(f"✗ Falsified:      {falsified}")
    print(f"⚠ Incomplete:     {incomplete}")
    print(f"⏱ Timeout:        {timeout}")
    print(f"? Error/Unknown:  {error}")
    
    total_time = sum(r['time'] for r in results)
    print(f"\nTotal time: {total_time:.2f}s ({total_time/60:.2f} minutes)")
    
    # Save to JSON if requested
    if output_json:
        output_path = Path(output_json)
        with open(output_path, 'w') as f:
            json.dump({
                'file': str(spthy_file),
                'timestamp': datetime.now().isoformat(),
                'total_lemmas': len(results),
                'verified': verified,
                'falsified': falsified,
                'incomplete': incomplete,
                'timeout': timeout,
                'error': error,
                'total_time': total_time,
                'results': results
            }, f, indent=2)
        print(f"\nResults saved to: {output_json}")
    
    return results

# Example usage
if __name__ == "__main__":
    import sys
    
    # if len(sys.argv) < 2:
    #     print("Usage: python tamarin_prover.py <file.spthy> [timeout_per_lemma] [output.json]")
    #     print("\nExample:")
    #     print("  python tamarin_prover.py model.spthy 300 results.json")
    #     sys.exit(1)
    
    spthy_file = "D:\\Academics\\LLM Guided Matter\\FSM_Generator\\codes\\fsm_models_v2\\1.5_OnOff_Cluster_fsm.spthy"
    timeout = 300
    output_json = None
    
    prove_all_lemmas(spthy_file, timeout, output_json)