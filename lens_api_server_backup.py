#!/usr/bin/env python3
"""
Lens Patent API Server with OpenAI Integration
Advanced patent search with LLM-generated queries
"""

from flask import Flask, request, jsonify
import requests
import json
import os
from pathlib import Path

# Load API keys from .env file
ENV_API_KEY = None
OPENAI_API_KEY = None

if Path('.env').exists():
    with open('.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('LENS_API_KEY='):
                ENV_API_KEY = line.split('=', 1)[1].strip('"\'')
            elif line.startswith('OPENAI_API_KEY='):
                OPENAI_API_KEY = line.split('=', 1)[1].strip('"\'')

if not ENV_API_KEY:
    print("⚠️  WARNING: LENS_API_KEY not found in .env file!")
if not OPENAI_API_KEY:
    print("⚠️  WARNING: OPENAI_API_KEY not found in .env file!")

app = Flask(__name__)

@app.route('/')
def home():
    return r'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Lens Patent API Client</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; color: #333; padding: 20px; }
            .container { max-width: 1600px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); overflow: hidden; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }
            .header h1 { font-size: 28px; margin-bottom: 8px; }
            .content { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; padding: 30px; }
            .section { display: flex; flex-direction: column; gap: 12px; }
            .section h3 { font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; color: #666; margin-top: 16px; }
            label { font-size: 13px; font-weight: 500; color: #333; display: block; margin-bottom: 4px; }
            input, textarea, select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-family: 'Courier New', monospace; font-size: 12px; background: #fafafa; }
            input:focus, textarea:focus, select:focus { outline: none; border-color: #667eea; background: white; }
            textarea { resize: vertical; min-height: 100px; }
            .button-row { display: flex; gap: 8px; margin-top: 8px; }
            button { flex: 1; padding: 10px 16px; border: 1px solid #ddd; background: white; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.2s; }
            button:hover { background: #f0f0f0; }
            button.primary { background: #667eea; color: white; border-color: #667eea; }
            button.primary:hover { background: #5568d3; }
            button:disabled { background: #ccc; color: #666; cursor: not-allowed; }
            .status { padding: 10px 12px; border-radius: 6px; font-size: 12px; display: none; margin-top: 8px; }
            .status.show { display: block; }
            .status.error { background: #ffebee; color: #d32f2f; border: 1px solid #ef5350; }
            .status.success { background: #e8f5e9; color: #388e3c; border: 1px solid #81c784; }
            .status.info { background: #e3f2fd; color: #1976d2; border: 1px solid #90caf9; }
            .response-area { border: 1px solid #ddd; border-radius: 6px; padding: 12px; background: #fafafa; max-height: 400px; overflow-y: auto; font-family: 'Courier New', monospace; font-size: 11px; white-space: pre-wrap; word-break: break-word; }
            .full-width { grid-column: 1 / -1; }
            .response-wrapper { grid-column: 1 / -1; margin-top: 20px; border-top: 1px solid #eee; padding-top: 20px; }
            #booleanMode { display: none; }
            .template-btn { padding: 6px 12px; font-size: 11px; border: 1px solid #ddd; background: white; border-radius: 4px; cursor: pointer; }
            .template-btn:hover { background: #f0f0f0; border-color: #667eea; }
            .result-info { background: #f0f4ff; border-left: 4px solid #667eea; padding: 12px; border-radius: 4px; font-size: 13px; margin: 12px 0; }
            .result-count { font-size: 16px; color: #667eea; font-weight: 600; }
            .column { flex: 1; }
            .column.full { grid-column: 1 / -1; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔍 Lens Patent API Client with AI</h1>
                <p>Advanced Patent Search with Boolean Queries & LLM-Generated Strategies</p>
            </div>
            <div class="content">
                <!-- LEFT COLUMN: AI QUERY GENERATOR -->
                <div class="column">
                    <div class="section">
                        <h3>AI Query Generator</h3>
                        
                        <label>Invention Description</label>
                        <textarea id="inventionDescription" placeholder="Describe your invention in detail. Example: A system for real-time monitoring of blood pressure using artificial intelligence to predict cardiovascular events. Include key features, technical aspects, and intended applications."></textarea>
                        
                        <label style="margin-top: 12px;">Prior Art Patents (Optional)</label>
                        <textarea id="priorArtPatents" placeholder="(Optional) Enter patent IDs that you know are related to your invention. Separate multiple patents with ;; (double semicolon).&#10;&#10;Supported formats: EP4301213, CN121190407, CA3241308, US7654321&#10;Or with spaces/underscores: EP 4301213, CN_121190407&#10;&#10;Example:&#10;EP4301213 ;; CN121190407 ;; CA3241308&#10;&#10;The system will search Lens for these patents to validate your generated query."></textarea>
                        
                        <div class="button-row">
                            <button onclick="searchPriorArt()" class="primary">Search Prior Art in Lens</button>
                            <button onclick="clearPriorArt()">Clear</button>
                        </div>
                        
                        <div id="priorArtSearchStatus" class="status" style="margin-top: 8px;"></div>
                        <div id="priorArtResults" style="margin-top: 12px; padding: 10px; background: #f0f4ff; border-radius: 4px; display: none;">
                            <h4 style="margin-top: 0;">Prior Art Identification Results:</h4>
                            <div id="priorArtResultsList" style="max-height: 200px; overflow-y: auto;"></div>
                        </div>
                        
                        <div class="button-row">
                            <button onclick="generateQuery()" class="primary">Generate Query</button>
                            <button onclick="clearAI()">Clear</button>
                        </div>
                        <div id="aiStatus" class="status"></div>
                        
                        <label style="margin-top: 12px;">Generated Query</label>
                        <textarea id="generatedQuery" placeholder="AI-generated boolean query will appear here..." readonly></textarea>
                        
                        <div id="validationStatus" class="status" style="margin-top: 8px;"></div>
                        
                        <div class="button-row">
                            <button onclick="copyGenerated()">Copy Generated</button>
                            <button onclick="useGenerated()">Use This Query</button>
                        </div>
                    </div>
                </div>

                <!-- CENTER COLUMN: MANUAL QUERY BUILDER -->
                <div class="column">
                    <div class="section">
                        <h3>Manual Query Builder</h3>
                        <label>Type</label>
                        <select id="mode" onchange="switchMode()">
                            <option value="boolean">Boolean Query</option>
                        </select>

                        <!-- BOOLEAN MODE -->
                        <div id="booleanMode">
                        </div>

                        <!-- BOOLEAN MODE -->
                        <div id="booleanMode">
                            <label style="margin-top: 12px;">Field(s)</label>
                            <select id="boolField">
                                <option value="biblio.invention_title">Title Only</option>
                                <option value="abstract">Abstract Only</option>
                                <option value="claims">Claims Only</option>
                                <option value="all">Title OR Abstract OR Claims</option>
                            </select>

                            <label style="margin-top: 12px;">Query</label>
                            <textarea id="boolQuery" placeholder="Example: compress* AND (device OR apparatus)"></textarea>
                        </div>

                        <label style="margin-top: 12px;">Classification Filters (Optional)</label>
                        <div style="font-size: 11px; color: #666; margin-bottom: 8px;">
                            Add IPC, CPC, or USPC codes to filter results. Examples: H02K1/00 or A61B
                        </div>
                        
                        <label style="font-size: 12px;">IPC Classification (optional)</label>
                        <textarea id="ipcCode" placeholder="e.g., A61B or H02K1/00&#10;Separate multiple codes with ;; (double semicolon)&#10;Example: A61B ;; H02K1/00 ;; A61M" style="min-height: 60px;"></textarea>
                        
                        <label style="font-size: 12px; margin-top: 8px;">CPC Classification (optional)</label>
                        <textarea id="cpcCode" placeholder="e.g., H02K1/00 or A61M&#10;Separate multiple codes with ;; (double semicolon)&#10;Example: H02K1/00 ;; A61B5/02 ;; A61M" style="min-height: 60px;"></textarea>

                        <label style="font-size: 12px; margin-top: 8px;">Exclusion Keywords (optional)</label>
                        <textarea id="exclusionKeywords" placeholder="Keywords to EXCLUDE from results&#10;Separate with ;; (double semicolon)&#10;Example: imaging ;; diabetes ;; glucose" style="min-height: 60px;"></textarea>

                        <label style="margin-top: 12px;">Sort (JSON)</label>
                        <textarea id="sort" style="min-height: 60px;">[{"created":"desc"}]</textarea>

                        <div class="button-row" style="margin-top: 12px;">
                            <button onclick="build()" class="primary">Build Request</button>
                            <button onclick="clearAll()">Clear</button>
                        </div>
                        <div id="buildStatus" class="status"></div>
                    </div>
                </div>

                <!-- RIGHT COLUMN: REQUEST & RESULTS -->
                <div class="column">
                    <div class="section">
                        <h3>Request & Execution</h3>
                        
                        <label>Request JSON</label>
                        <textarea id="requestBody" placeholder="Your request will appear here..."></textarea>
                        
                        <div class="button-row">
                            <button onclick="copyReq()">Copy</button>
                            <button onclick="downReq()">Download</button>
                        </div>

                        <label style="margin-top: 12px;">Results Size</label>
                        <input type="number" id="size" value="10" min="1" max="100">

                        <div class="button-row" style="margin-top: 12px;">
                            <button onclick="getCount()" class="primary">Check Count</button>
                        </div>
                        <div id="countStatus" class="status"></div>
                        <div id="countInfo"></div>

                        <div id="retrieveSection" style="display: none; margin-top: 12px;">
                            <div class="button-row">
                                <button onclick="send()" class="primary">Retrieve Results</button>
                                <button onclick="exportHTML()" class="primary" style="background: #28a745;">Export to HTML</button>
                                <button onclick="clearResp()">Clear</button>
                            </div>
                        </div>
                        
                        <div id="sendStatus" class="status" style="margin-top: 12px;"></div>
                        
                        <label style="margin-top: 12px;">Response</label>
                        <div class="response-area" id="response">Ready...</div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            let lastCountResult = null;

            function switchMode() {
                // Only boolean mode now, always show it
                document.getElementById('booleanMode').style.display = 'block';
            }

            async function searchPriorArt() {
                const priorArtText = document.getElementById('priorArtPatents').value.trim();
                if (!priorArtText) { 
                    alert('Enter at least one patent ID'); 
                    return; 
                }

                const patentIds = priorArtText.split(';;').map(id => id.trim()).filter(id => id);
                const st = document.getElementById('priorArtSearchStatus');
                const resultsDiv = document.getElementById('priorArtResults');
                const resultsList = document.getElementById('priorArtResultsList');

                st.textContent = `⏳ Searching Lens for ${patentIds.length} patent(s)...`;
                st.className = 'status show info';
                resultsDiv.style.display = 'none';
                resultsList.innerHTML = '';

                try {
                    const res = await fetch('/api/search-prior-art', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({patentIds: patentIds})
                    });

                    const data = await res.json();
                    if (res.ok) {
                        const results = data.results || [];
                        window.identifiedPatents = results;

                        let html = '';
                        let foundCount = 0;
                        let notFoundCount = 0;

                        results.forEach((result, idx) => {
                            if (result.found) {
                                foundCount++;
                                html += `<div style="margin: 10px 0; padding: 10px; background: white; border-left: 4px solid #28a745; border-radius: 4px;"><strong style="color: #28a745;">✅ Patent ${idx + 1} FOUND</strong><br><strong>Patent ID:</strong> ${result.patentId}<br><strong>Lens ID:</strong> ${result.lens_id}<br><strong>Title:</strong> ${result.title}<br><small style="color: #666;">Country: ${result.country || 'N/A'}</small></div>`;
                            } else {
                                notFoundCount++;
                                html += `<div style="margin: 10px 0; padding: 10px; background: white; border-left: 4px solid #dc3545; border-radius: 4px;"><strong style="color: #dc3545;">❌ Patent ${idx + 1} NOT FOUND</strong><br><strong>Patent ID:</strong> ${result.patentId}<br><small style="color: #666;">The system could not find this patent in Lens. Check the patent ID format: EP4301213, CN121190407, CA3241308, US7654321</small></div>`;
                            }
                        });

                        resultsList.innerHTML = html;
                        resultsDiv.style.display = 'block';

                        if (notFoundCount === 0) {
                            st.textContent = `✅ Success! All ${foundCount} patents identified in Lens.`;
                            st.className = 'status show success';
                        } else {
                            st.textContent = `⚠️ Found ${foundCount}/${patentIds.length} patents. ${notFoundCount} not found - please check the IDs and retry.`;
                            st.className = 'status show warning';
                        }
                    } else {
                        st.textContent = `❌ Error: ${data.error}`;
                        st.className = 'status show error';
                    }
                } catch (e) {
                    st.textContent = '❌ Search failed: ' + e.message;
                    st.className = 'status show error';
                }
            }

            function clearPriorArt() {
                document.getElementById('priorArtPatents').value = '';
                document.getElementById('priorArtSearchStatus').textContent = '';
                document.getElementById('priorArtResults').style.display = 'none';
                window.identifiedPatents = [];
            }

            async function generateQuery() {
                const inventionDesc = document.getElementById('inventionDescription').value.trim();
                const priorArt = document.getElementById('priorArtPatents').value.trim();
                
                if (!inventionDesc) { alert('Enter an invention description'); return; }

                const st = document.getElementById('aiStatus');
                const vs = document.getElementById('validationStatus');
                
                st.textContent = '⏳ Generating query with AI...';
                st.className = 'status show info';
                vs.textContent = '';

                try {
                    // Build patent details from identified patents
                    let patentDetails = '';
                    if (window.identifiedPatents && window.identifiedPatents.length > 0) {
                        const foundPatents = window.identifiedPatents.filter(p => p.found);
                        if (foundPatents.length > 0) {
                            patentDetails = '\n\nPRIOR ART PATENT DETAILS (for keyword extraction):\n';
                            foundPatents.forEach((patent, idx) => {
                                patentDetails += `${idx + 1}. ${patent.patentId} (${patent.country})\n   Title: ${patent.title}\n`;
                            });
                        }
                    }

                    const res = await fetch('/api/generate-query', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            invention: inventionDesc,
                            priorArt: priorArt,
                            patentDetails: patentDetails
                        })
                    });

                    const data = await res.json();
                    if (res.ok) {
                        document.getElementById('generatedQuery').value = data.query;
                        st.textContent = '✅ Query generated!';
                        st.className = 'status show success';
                        
                        // If prior art patents identified, validate and potentially refine
                        if (window.identifiedPatents && window.identifiedPatents.length > 0) {
                            const foundPatents = window.identifiedPatents.filter(p => p.found);
                            if (foundPatents.length > 0) {
                                await validateAndRefineQuery(data.query, foundPatents);
                            }
                        }
                    } else {
                        st.textContent = `❌ Error: ${data.error}`;
                        st.className = 'status show error';
                    }
                } catch (e) {
                    st.textContent = '❌ Failed: ' + e.message;
                    st.className = 'status show error';
                }
            }


            async function validateAndRefineQuery(query, foundPatents) {
                const vs = document.getElementById('validationStatus');
                const maxIterations = 3;
                let currentQuery = query;
                let iteration = 0;

                vs.innerHTML = '⏳ Iteration 1: Validating query against ' + foundPatents.length + ' prior art patents...';
                vs.className = 'status show info';

                while (iteration < maxIterations) {
                    iteration++;
                    console.log('=== ITERATION ' + iteration + ' ===');
                    console.log('Current query:', currentQuery);
                    
                    const validationResult = await validateQueryAgainstPatents(currentQuery, foundPatents);
                    console.log('Validation result:', validationResult);
                    
                    if (validationResult.foundCount === foundPatents.length) {
                        vs.innerHTML = '✅ <strong>Validation SUCCESS!</strong><br>All ' + foundPatents.length + ' prior art patents found!<br>Query is ready to use.';
                        vs.className = 'status show success';
                        console.log('SUCCESS: All patents found!');
                        return;
                    } else if (iteration < maxIterations) {
                        const missingLensIds = validationResult.missingLensIds;
                        console.log('Missing Lens IDs:', missingLensIds);
                        
                        vs.innerHTML = '⚠️ Iteration ' + iteration + ': Found ' + validationResult.foundCount + '/' + foundPatents.length + ' patents. Extracting keywords from ' + missingLensIds.length + ' missing patent(s)...';
                        vs.className = 'status show warning';
                        
                        const patentDetails = await getPatentDetailsForRefinement(missingLensIds);
                        console.log('Patent details retrieved:', patentDetails);
                        
                        const refinedQuery = await generateRefinedQuery(currentQuery, patentDetails);
                        console.log('Refined query:', refinedQuery);
                        
                        currentQuery = refinedQuery;
                        document.getElementById('generatedQuery').value = currentQuery;
                        
                        if (iteration < maxIterations) {
                            vs.innerHTML = '⏳ Iteration ' + (iteration + 1) + ': Re-validating refined query...';
                            vs.className = 'status show info';
                        }
                    }
                }

                console.log('=== FINAL VALIDATION ===');
                const finalValidation = await validateQueryAgainstPatents(currentQuery, foundPatents);
                console.log('Final validation result:', finalValidation);
                
                if (finalValidation.foundCount === foundPatents.length) {
                    vs.innerHTML = '✅ <strong>Validation SUCCESS after ' + iteration + ' iterations!</strong><br>All ' + foundPatents.length + ' prior art patents found!<br>Query has been refined and is ready to use.';
                    vs.className = 'status show success';
                } else {
                    vs.innerHTML = '⚠️ <strong>Validation PARTIAL after ' + iteration + ' iterations:</strong><br>Found ' + finalValidation.foundCount + '/' + foundPatents.length + ' patents.<br>Consider refining the query manually or using different prior art patents.';
                    vs.className = 'status show warning';
                }
            }

            async function validateQueryAgainstPatents(query, foundPatents) {
                try {
                    const tokens = tokenize(query);
                    const queryObj = parseQuery(tokens, 'abstract');

                    const req = {
                        query: queryObj,
                        size: 100,
                        from: 0,
                        _source: {includes: ['lens_id']}
                    };

                    const res = await fetch('/api/search', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({request: req})
                    });

                    const data = await res.json();
                    if (res.ok && data.response && data.response.data) {
                        const results = data.response.data;
                        const resultLensIds = results.map(p => p.lens_id).filter(id => id);

                        let foundCount = 0;
                        let foundLensIds = [];
                        let missingLensIds = [];

                        foundPatents.forEach(patent => {
                            if (resultLensIds.includes(patent.lens_id)) {
                                foundCount++;
                                foundLensIds.push(patent.lens_id);
                            } else {
                                missingLensIds.push(patent.lens_id);
                            }
                        });

                        return { foundCount: foundCount, foundLensIds: foundLensIds, missingLensIds: missingLensIds };
                    } else {
                        return { foundCount: 0, foundLensIds: [], missingLensIds: foundPatents.map(p => p.lens_id) };
                    }
                } catch (e) {
                    console.error('Validation error:', e);
                    return { foundCount: 0, foundLensIds: [], missingLensIds: foundPatents.map(p => p.lens_id) };
                }
            }

            async function getPatentDetailsForRefinement(lensIds) {
                try {
                    console.log('getPatentDetailsForRefinement called with Lens IDs:', lensIds);
                    
                    const res = await fetch('/api/get-patent-details', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({lensIds: lensIds})
                    });

                    console.log('Fetch response status:', res.status, res.ok);
                    
                    const data = await res.json();
                    console.log('Fetch response data:', data);
                    
                    const results = data.results || [];
                    console.log('Results count:', results.length);
                    
                    console.log('PATENT TITLES AND ABSTRACTS:');
                    results.forEach(function(r, idx) {
                        console.log('\nPatent ' + (idx+1) + ' - ' + r.lens_id);
                        console.log('Title: ' + r.title);
                        console.log('Abstract (first 200 chars): ' + (r.abstract ? r.abstract.substring(0, 200) : 'N/A'));
                    });
                    
                    console.log('Returning results');
                    return results;
                } catch (e) {
                    console.error('Error in getPatentDetailsForRefinement:', e);
                    return [];
                }
            }

            async function generateRefinedQuery(currentQuery, patentDetails) {
                try {
                    let allKeywords = [];
                    
                    patentDetails.forEach(patent => {
                        if (patent.found && (patent.title || patent.abstract)) {
                            const text = (patent.title + ' ' + patent.abstract).toLowerCase();
                            const words = text.match(/\b\w{4,}\b/g) || [];
                            
                            const stopwords = ['that', 'with', 'from', 'this', 'have', 'been', 'are', 'will', 'can', 'may', 'such', 'system', 'method', 'device', 'patent', 'invention', 'invention', 'disclosed'];
                            const filtered = words.filter(w => !stopwords.includes(w));
                            
                            allKeywords.push(...filtered);
                        }
                    });

                    const keywordCounts = {};
                    allKeywords.forEach(kw => {
                        keywordCounts[kw] = (keywordCounts[kw] || 0) + 1;
                    });

                    const topKeywords = Object.entries(keywordCounts)
                        .sort((a, b) => b[1] - a[1])
                        .slice(0, 4)
                        .map(entry => entry[0]);

                    if (topKeywords.length === 0) return currentQuery;

                    console.log('Extracted keywords:', topKeywords);

                    const keywordGroup = '(' + topKeywords.join(' OR ') + ')';
                    const refinedQuery = currentQuery + ' AND ' + keywordGroup;

                    console.log('Refined query:', refinedQuery);
                    return refinedQuery;
                } catch (e) {
                    console.error('Error in generateRefinedQuery:', e);
                    return currentQuery;
                }
            }

            function useGenerated() {
                const q = document.getElementById('generatedQuery').value.trim();
                if (!q) { alert('Generate a query first'); return; }
                
                document.getElementById('mode').value = 'boolean';
                document.getElementById('boolField').value = 'all';
                document.getElementById('boolQuery').value = q;
                switchMode();
                build();
            }

            function copyGenerated() {
                const q = document.getElementById('generatedQuery').value;
                if (!q) return alert('Generate query first');
                navigator.clipboard.writeText(q);
            }

            function clearAI() {
                document.getElementById('inventionDescription').value = '';
                document.getElementById('priorArtPatents').value = '';
                document.getElementById('generatedQuery').value = '';
                document.getElementById('aiStatus').textContent = '';
                document.getElementById('validationStatus').textContent = '';
            }

            // Parse boolean query
            function parseQuery(tokens, field) {
                let pos = 0;
                const peek = () => tokens[pos];
                const take = () => tokens[pos++];

                const parseOr = () => {
                    let l = parseAnd();
                    while (peek() === 'OR') {
                        take();
                        const r = parseAnd();
                        l = {bool: {should: [l, r], minimum_should_match: 1}};
                    }
                    return l;
                };

                const parseAnd = () => {
                    let l = parseNot();
                    while (peek() === 'AND') {
                        take();
                        const r = parseNot();
                        if (l.bool && l.bool.must) {
                            l.bool.must.push(r);
                        } else {
                            l = {bool: {must: [l, r]}};
                        }
                    }
                    return l;
                };

                const parseNot = () => {
                    if (peek() === 'NOT') {
                        take();
                        return {bool: {must_not: [parsePrim()]}};
                    }
                    return parsePrim();
                };

                const parsePrim = () => {
                    if (peek() === '(') {
                        take();
                        const e = parseOr();
                        take();
                        return e;
                    }
                    return makeTerm(take(), field);
                };

                const makeTerm = (t, f) => {
                    if (!t) throw new Error('Unexpected end');
                    const m = t.match(/^"(.+?)"~(\d+)$/);
                    if (m) return {match_phrase: {[f]: {query: m[1], slop: parseInt(m[2])}}};
                    if (t.startsWith('"') && t.endsWith('"')) return {match_phrase: {[f]: t.slice(1, -1)}};
                    if (t.includes('*') || t.includes('?')) return {wildcard: {[f]: {value: t.toLowerCase()}}};
                    return {match: {[f]: t}};
                };

                return parseOr();
            }

            function tokenize(s) {
                let tokens = [], cur = '', inQ = false;
                for (let i = 0; i < s.length; i++) {
                    const c = s[i];
                    if (c === '"') { inQ = !inQ; cur += c; }
                    else if (inQ) { cur += c; }
                    else if ('()'.includes(c)) { if (cur.trim()) tokens.push(cur.trim()); tokens.push(c); cur = ''; }
                    else if (c === ' ') { if (cur.trim()) tokens.push(cur.trim()); cur = ''; }
                    else { cur += c; }
                }
                if (cur.trim()) tokens.push(cur.trim());
                return tokens;
            }

            function build() {
                try {
                    const mode = document.getElementById('mode').value;
                    let q = {};

                    if (mode === 'simple') {
                        const t = document.getElementById('simpleTerm').value.trim();
                        const f = document.getElementById('searchField').value;
                        if (!t) throw new Error('Enter search term');
                        
                        if (f === 'all') {
                            const fields = ['biblio.invention_title', 'abstract', 'claims'];
                            const queries = fields.map(field => ({match: {[field]: t}}));
                            q = {bool: {should: queries, minimum_should_match: 1}};
                        } else {
                            q = {match: {[f]: t}};
                        }
                    } else {
                        const qstr = document.getElementById('boolQuery').value.trim();
                        const fieldOpt = document.getElementById('boolField').value;
                        if (!qstr) throw new Error('Enter query');
                        const toks = tokenize(qstr);
                        
                        if (fieldOpt === 'all') {
                            // Parse the same query for each field, then combine with OR (should)
                            const fields = ['biblio.invention_title', 'abstract', 'claims'];
                            const queries = fields.map(f => parseQuery(toks.slice(), f));
                            q = {bool: {should: queries, minimum_should_match: 1}};
                        } else {
                            q = parseQuery(toks, fieldOpt);
                        }
                    }

                    // Parse classification codes
                    const sz = parseInt(document.getElementById('size').value) || 10;
                    const so = JSON.parse(document.getElementById('sort').value);
                    
                    const ipcInput = document.getElementById('ipcCode').value.trim();
                    const cpcInput = document.getElementById('cpcCode').value.trim();
                    const exclusionInput = document.getElementById('exclusionKeywords').value.trim();
                    
                    const ipcCodes = ipcInput ? ipcInput.split(';;').map(c => c.trim()).filter(c => c) : [];
                    const cpcCodes = cpcInput ? cpcInput.split(';;').map(c => c.trim()).filter(c => c) : [];
                    const exclusionKeywords = exclusionInput ? exclusionInput.split(';;').map(c => c.trim()).filter(c => c) : [];
                    
                    let req = {
                        query: q,
                        size: sz,
                        from: 0,
                        _source: {
                            includes: ['biblio.invention_title', 'legal_status', 'biblio.priority_claims', 'abstract', 'biblio.classifications_ipc', 'biblio.classifications_cpc']
                        },
                        sort: so
                    };
                    
                    // Build must_not clause for exclusion keywords
                    let mustNotClauses = [];
                    exclusionKeywords.forEach(keyword => {
                        mustNotClauses.push({match: {'biblio.invention_title': keyword}});
                        mustNotClauses.push({match: {'abstract': keyword}});
                        mustNotClauses.push({match: {'claims': keyword}});
                    });
                    
                    // If classifications are provided, add them using query_string filter
                    if (ipcCodes.length > 0 || cpcCodes.length > 0) {
                        let queryParts = [];
                        
                        // Build query string for IPC codes
                        ipcCodes.forEach(code => {
                            queryParts.push('class_ipcr.symbol:' + code + '*');
                        });
                        
                        // Build query string for CPC codes
                        cpcCodes.forEach(code => {
                            queryParts.push('class_cpc.symbol:' + code + '*');
                        });
                        
                        // Combine with OR if multiple codes
                        const filterQuery = queryParts.join(' OR ');
                        
                        if (filterQuery) {
                            req.query = {
                                bool: {
                                    must: [q],
                                    filter: {
                                        query_string: {
                                            query: filterQuery
                                        }
                                    }
                                }
                            };
                            if (mustNotClauses.length > 0) {
                                req.query.bool.must_not = mustNotClauses;
                            }
                        }
                    } else if (mustNotClauses.length > 0) {
                        // If only exclusions without classifications
                        req.query = {
                            bool: {
                                must: [q],
                                must_not: mustNotClauses
                            }
                        };
                    }

                    document.getElementById('requestBody').value = JSON.stringify(req, null, 2);
                    const s = document.getElementById('buildStatus');
                    s.textContent = '✅ Request built. Check count next.';
                    s.className = 'status show success';
                    
                    document.getElementById('countInfo').innerHTML = '';
                    document.getElementById('retrieveSection').style.display = 'none';
                } catch (e) {
                    const s = document.getElementById('buildStatus');
                    s.textContent = '❌ ' + e.message;
                    s.className = 'status show error';
                }
            }

            async function getCount() {
                const r = document.getElementById('requestBody').value.trim();
                if (!r) { alert('Build request first'); return; }

                const st = document.getElementById('countStatus');
                st.textContent = '⏳ Counting...';
                st.className = 'status show info';

                try {
                    const res = await fetch('/api/count', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({request: JSON.parse(r)})
                    });

                    const data = await res.json();
                    if (res.ok) {
                        const total = data.total;
                        const resultSize = parseInt(document.getElementById('size').value) || 10;
                        
                        let infoHtml = `<div class="result-info">
                            <strong>Total: <span class="result-count">${total.toLocaleString()}</span></strong>
                            Retrieving ${Math.min(resultSize, total)} results
                        </div>`;
                        
                        document.getElementById('countInfo').innerHTML = infoHtml;
                        document.getElementById('retrieveSection').style.display = 'block';
                        st.textContent = `✅ Found ${total.toLocaleString()}`;
                        st.className = 'status show success';
                    } else {
                        st.textContent = `❌ Error: ${data.error}`;
                        st.className = 'status show error';
                    }
                } catch (e) {
                    st.textContent = '❌ Failed: ' + e.message;
                    st.className = 'status show error';
                }
            }

            function copyReq() {
                const r = document.getElementById('requestBody').value;
                if (!r) return alert('Build first');
                navigator.clipboard.writeText(r);
            }

            function downReq() {
                const r = document.getElementById('requestBody').value;
                if (!r) return alert('Build first');
                const b = new Blob([r], {type: 'application/json'});
                const u = URL.createObjectURL(b);
                const a = document.createElement('a');
                a.href = u;
                a.download = 'lens_request.json';
                a.click();
            }

            function clearAll() {
                document.getElementById('simpleTerm').value = '';
                document.getElementById('boolQuery').value = '';
                document.getElementById('requestBody').value = '';
                document.getElementById('countInfo').innerHTML = '';
                document.getElementById('retrieveSection').style.display = 'none';
            }

            function clearResp() {
                document.getElementById('response').textContent = 'Ready...';
            }

            async function send() {
                const r = document.getElementById('requestBody').value.trim();
                if (!r) { alert('Build first'); return; }

                const resp = document.getElementById('response');
                resp.textContent = 'Retrieving...';
                const st = document.getElementById('sendStatus');
                st.textContent = '⏳ Retrieving...';
                st.className = 'status show info';

                try {
                    const res = await fetch('/api/search', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({request: JSON.parse(r)})
                    });

                    const data = await res.json();
                    if (res.ok) {
                        resp.textContent = JSON.stringify(data.response, null, 2);
                        const c = data.response?.data?.length || 0;
                        st.textContent = `✅ Retrieved ${c} results`;
                        st.className = 'status show success';
                    } else {
                        resp.textContent = JSON.stringify(data, null, 2);
                        st.textContent = `❌ Error: ${data.error}`;
                        st.className = 'status show error';
                    }
                } catch (e) {
                    resp.textContent = 'Error: ' + e.message;
                    st.textContent = '❌ Failed: ' + e.message;
                    st.className = 'status show error';
                }
            }

            function exportHTML() {
                const responseText = document.getElementById('response').textContent;
                if (!responseText || responseText === 'Ready...') { alert('No results to export'); return; }
                
                try {
                    const data = JSON.parse(responseText);
                    const patents = data.data || [];
                    
                    let html = `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Patent Search Results</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; }
        .patent { margin: 20px 0; padding: 15px; border-left: 4px solid #667eea; background: #f9f9f9; }
        .patent h3 { margin: 0 0 10px 0; color: #667eea; }
        .field { margin: 8px 0; }
        .label { font-weight: bold; color: #666; }
        .value { color: #333; margin-left: 10px; }
        .classifications { background: #f0f4ff; padding: 10px; border-radius: 4px; margin: 10px 0; }
        .ipc { color: #667eea; font-weight: bold; }
        .cpc { color: #764ba2; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Patent Search Results</h1>
        <p>Total Results: <strong>${patents.length}</strong></p>
        <hr>
`;
                    
                    patents.forEach((patent, index) => {
                        const title = patent.biblio?.invention_title?.[0]?.text || 'N/A';
                        const abstract = patent.abstract?.[0]?.text || 'N/A';
                        const status = patent.legal_status?.patent_status || 'N/A';
                        const ipc = patent.biblio?.classifications_ipc?.main_classification || 'N/A';
                        const cpc = patent.biblio?.classifications_cpc?.symbol || 'N/A';
                        const lensId = patent.lens_id || 'N/A';
                        
                        html += `
        <div class="patent">
            <h3>${index + 1}. ${title}</h3>
            <div class="field">
                <span class="label">Lens ID:</span>
                <span class="value">${lensId}</span>
            </div>
            <div class="field">
                <span class="label">Status:</span>
                <span class="value">${status}</span>
            </div>
            <div class="classifications">
                <div class="field">
                    <span class="ipc">IPC: ${ipc}</span>
                </div>
                <div class="field">
                    <span class="cpc">CPC: ${cpc}</span>
                </div>
            </div>
            <div class="field">
                <span class="label">Abstract:</span>
                <div class="value">${abstract}</div>
            </div>
        </div>
`;
                    });
                    
                    html += `
    </div>
</body>
</html>`;
                    
                    const blob = new Blob([html], {type: 'text/html'});
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'patent_results_' + new Date().toISOString().slice(0,10) + '.html';
                    a.click();
                } catch (e) {
                    alert('Error exporting: ' + e.message);
                }
            }

            window.onload = () => { 
                switchMode(); 
                build();
            };
        </script>
    </body>
    </html>
    '''

@app.route('/api/get-patent-details', methods=['POST'])
def get_patent_details():
    """Fetch full patent details by Lens ID for keyword extraction"""
    try:
        if not ENV_API_KEY:
            return jsonify({'error': 'Lens API key not configured'}), 400

        data = request.get_json() or {}
        lens_ids = data.get('lensIds', [])

        if not lens_ids:
            return jsonify({'error': 'No Lens IDs provided'}), 400

        import time
        results = []
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {ENV_API_KEY}'}

        for idx, lens_id in enumerate(lens_ids):
            if idx > 0:
                time.sleep(0.3)
            
            search_request = {
                "query": {"match": {"lens_id": lens_id}},
                "size": 1,
                "from": 0,
                "_source": {"includes": ["lens_id", "biblio.invention_title", "abstract"]}
            }

            try:
                response = requests.post('https://api.lens.org/patent/search', json=search_request, headers=headers, timeout=30)

                if response.status_code == 200:
                    response_data = response.json()
                    patents = response_data.get('data', [])

                    if patents:
                        patent = patents[0]
                        title = patent.get('biblio', {}).get('invention_title', [{}])[0].get('text', '') if isinstance(patent.get('biblio', {}).get('invention_title'), list) else ''
                        abstract = patent.get('abstract', [{}])[0].get('text', '') if isinstance(patent.get('abstract'), list) else ''
                        
                        results.append({'lens_id': lens_id, 'title': title, 'abstract': abstract, 'found': True})
                    else:
                        results.append({'lens_id': lens_id, 'found': False})
                else:
                    results.append({'lens_id': lens_id, 'found': False})
            except:
                results.append({'lens_id': lens_id, 'found': False})

        return jsonify({'results': results}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search-prior-art', methods=['POST'])
def search_prior_art():
    """Search Lens database to identify patents by their IDs"""
    try:
        if not ENV_API_KEY:
            return jsonify({'error': 'Lens API key not configured'}), 400

        data = request.get_json() or {}
        patent_ids = data.get('patentIds', [])

        if not patent_ids:
            return jsonify({'error': 'No patent IDs provided'}), 400

        import time
        results = []
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {ENV_API_KEY}'}

        for idx, patent_id in enumerate(patent_ids):
            # Add delay between requests to respect rate limits (0.5 second)
            if idx > 0:
                time.sleep(0.5)
            
            # Search using the 'ids' field as documented in Lens API
            search_request = {
                "query": {
                    "match": {
                        "ids": patent_id
                    }
                },
                "size": 1,
                "from": 0,
                "_source": {
                    "includes": ["lens_id", "country", "doc_number", "kind", "biblio.invention_title"]
                }
            }

            try:
                response = requests.post(
                    'https://api.lens.org/patent/search',
                    json=search_request,
                    headers=headers,
                    timeout=30
                )

                if response.status_code == 200:
                    response_data = response.json()
                    patents = response_data.get('data', [])

                    if patents:
                        # Found the patent
                        best_match = patents[0]
                        results.append({
                            'found': True,
                            'patentId': patent_id,
                            'lens_id': best_match.get('lens_id', 'N/A'),
                            'title': best_match.get('biblio', {}).get('invention_title', [{}])[0].get('text', 'N/A') if isinstance(best_match.get('biblio', {}).get('invention_title'), list) else 'N/A',
                            'country': best_match.get('country', 'N/A'),
                            'doc_number': best_match.get('doc_number', 'N/A'),
                            'kind': best_match.get('kind', 'N/A')
                        })
                    else:
                        # Patent not found
                        results.append({
                            'found': False,
                            'patentId': patent_id,
                            'lens_id': None,
                            'title': None,
                            'country': None
                        })
                else:
                    # API error
                    results.append({
                        'found': False,
                        'patentId': patent_id,
                        'lens_id': None,
                        'title': None,
                        'country': None
                    })
            except Exception as e:
                results.append({
                    'found': False,
                    'patentId': patent_id,
                    'lens_id': None,
                    'title': None,
                    'country': None
                })

        return jsonify({'results': results}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate-query', methods=['POST'])
def generate_query():
    """Generate a boolean search query from invention description and optional prior art patents"""
    try:
        if not OPENAI_API_KEY:
            return jsonify({'error': 'OpenAI API key not configured'}), 400

        data = request.get_json() or {}
        invention = data.get('invention', '').strip()
        prior_art = data.get('priorArt', '').strip()
        patent_details = data.get('patentDetails', '').strip()

        if not invention:
            return jsonify({'error': 'No invention description provided'}), 400

        system_prompt = """You are a patent search specialist creating precise boolean search queries.

YOUR TASK:
Create ONE boolean query to find relevant patents based on an invention description.
If prior art patents are provided WITH their details, analyze their titles and abstracts to extract SHARED keywords.

STRATEGY:
1. Extract KEY FUNCTIONAL concepts from invention description (what does it do?)
2. Extract KEY STRUCTURAL concepts (what is it made of?)
3. Extract KEY TECHNICAL concepts (how does it work?)
4. If prior art details provided: ALSO extract keywords from those patent titles/abstracts
5. Combine all concepts: group alternatives with OR, combine groups with AND
6. Focus on words that would retrieve the prior art patents (use keywords FROM those patents)

CRITICAL RULES - FOLLOW EXACTLY:
1. INSIDE parentheses: ONLY use OR operators. NEVER use AND inside parentheses.
2. BETWEEN parentheses: Use AND to connect groups
3. NEVER mix AND and OR within the same group
4. Structure: (term1 OR term2 OR term3) AND (term4 OR term5) AND (term6 OR term7)

FORBIDDEN PATTERNS (DO NOT USE):
❌ (word1 OR word2 AND word3)  ← WRONG: AND inside parentheses
❌ (word1 AND word2 OR word3)  ← WRONG: AND inside parentheses
❌ word1 OR word2 AND word3 ← WRONG: mixed operators without grouping

CORRECT PATTERN:
✅ (monitoring OR detection OR surveillance) AND ("blood pressure" OR "cardiovascular") AND ("artificial intelligence" OR "machine learning")

EXAMPLES OF CORRECT QUERIES:
- (compression OR squeezing OR pressing) AND (bracelet OR wristband OR strap) AND (adjustment OR control)
- (monitoring OR detection) AND ("blood pressure" OR "vascular") AND (device OR apparatus)
- (heating OR insulation OR thermal) AND (building OR wall OR panel) AND (system OR structure)

GUIDELINES FOR SUCCESS:
- Extract actual keywords FROM the prior art patents if provided
- Each concept group gets parentheses with ONLY OR inside
- Groups connected with AND only
- Use word* for variations (e.g., compress* for compress, compression, compressed)
- Use "phrase"~2 for proximity searches (less common, use sparingly)
- Limit to 3-4 groups maximum
- MOST IMPORTANT: Use keywords that actually appear in the prior art patents
- Make the query specific enough to find those exact patents

Output ONLY the query string, nothing else. Do NOT explain. Do NOT use AND inside any parentheses."""

        if patent_details:
            user_message = f"""INVENTION DESCRIPTION:
{invention}

{patent_details}

TASK: Create a search query that will retrieve these prior art patents and others like them.
Extract keywords from the patent titles above and from the invention description.
Your query MUST find the patents listed above."""
        elif prior_art:
            user_message = f"""INVENTION DESCRIPTION:
{invention}

PRIOR ART PATENT IDs (examples of patents your query should find):
{prior_art}

Create a search query that would retrieve patents similar to the above invention and examples."""
        else:
            user_message = f"""INVENTION DESCRIPTION:
{invention}

Create a search query that would retrieve patents related to this invention."""

        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={'Authorization': f'Bearer {OPENAI_API_KEY}'},
            json={
                'model': 'gpt-4o',
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_message}
                ],
                'temperature': 0.3,
                'max_tokens': 300
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            query = result['choices'][0]['message']['content'].strip()
            return jsonify({'query': query}), 200
        else:
            try:
                error_detail = response.json()
                error_msg = error_detail.get('error', {}).get('message', f'HTTP {response.status_code}')
            except:
                error_msg = response.text or f'HTTP {response.status_code}'
            return jsonify({'error': f'OpenAI error: {error_msg}'}), response.status_code

    except Exception as e:
        return jsonify({'error': f'Exception: {str(e)}'}), 500

@app.route('/api/count', methods=['POST'])
def count():
    """Count total matching results"""
    try:
        if not ENV_API_KEY:
            return jsonify({'error': 'Lens API key not configured'}), 400

        data = request.get_json() or {}
        search_request = data.get('request')

        if not search_request:
            return jsonify({'error': 'Request required'}), 400

        count_request = {
            'query': search_request.get('query'),
            'size': 0
        }

        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {ENV_API_KEY}'}
        response = requests.post('https://api.lens.org/patent/search', json=count_request, headers=headers, timeout=30)

        if response.status_code == 200:
            result = response.json()
            total = result.get('total', 0)
            return jsonify({'total': total}), 200
        else:
            try:
                error_data = response.json()
            except:
                error_data = response.text
            return jsonify({'error': f'API error {response.status_code}'}), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search', methods=['POST'])
def search():
    """Retrieve actual results"""
    try:
        if not ENV_API_KEY:
            return jsonify({'error': 'Lens API key not configured'}), 400

        data = request.get_json() or {}
        search_request = data.get('request')

        if not search_request:
            return jsonify({'error': 'Request required'}), 400

        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {ENV_API_KEY}'}
        response = requests.post('https://api.lens.org/patent/search', json=search_request, headers=headers, timeout=30)

        if response.status_code == 200:
            return jsonify({'response': response.json()}), 200
        else:
            try:
                error_data = response.json()
            except:
                error_data = response.text
            return jsonify({'error': f'API error {response.status_code}'}), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    status = "✅ Both APIs configured" if (ENV_API_KEY and OPENAI_API_KEY) else "⚠️  Check .env file"
    print(f"\n🚀 Lens Patent API Client with AI\n📍 http://localhost:5000\n{status}\n")
    app.run(debug=False, host='127.0.0.1', port=5000)
