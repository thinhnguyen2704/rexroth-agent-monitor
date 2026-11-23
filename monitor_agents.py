import json
import os
import urllib.request
import urllib.error
from datetime import datetime

# Configurations
HISTORY_FILE = "agent_history.json"
DASHBOARD_FILE = "index.html"

SITES = {
    "India": {
        "url": "https://www.boschrexroth.com/en/in/",
        "endpoint": "https://cx.bosch-so.com/rexroth-chat-IN-ready",
        "key": "GP_Bosch_Rexroth_Chat_IN_VAG"
    },
    "Romania": {
        "url": "https://www.boschrexroth.com/ro/ro/",
        "endpoint": "https://cx.bosch-so.com/rexroth-chat-RO-ready",
        "key": "GP_Bosch_Rexroth_Chat_RO_VAG"
    },
    "Hungary": {
        "url": "https://www.boschrexroth.com/hu/hu/",
        "endpoint": "https://cx.bosch-so.com/rexroth-chat-HU-ready",
        "key": "GP_Bosch_Rexroth_Chat_HU_VAG"
    },
    "Czech Republic": {
        "url": "https://www.boschrexroth.com/cs/cz/",
        "endpoint": "https://cx.bosch-so.com/rexroth-chat-CZ-ready",
        "key": "GP_Bosch_Rexroth_Chat_CZ_VAG"
    },
    "Mexico": {
        "url": "https://www.boschrexroth.com/es/mx/",
        "endpoint": "https://cx.bosch-so.com/rexroth-chat-MX-ready",
        "key": "GP_Bosch_Rexroth_Chat_MX_VAG"
    }
}

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)

def check_availability():
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    hour_str = now.strftime("%H:00")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*'
    }
    
    history = load_history()
    if today_str not in history:
        history[today_str] = {}

    for country, info in SITES.items():
        if country not in history[today_str]:
            history[today_str][country] = {}
            
        status = "Offline"
        agents = -1 # -1 signifies error / unreachable
        
        try:
            req = urllib.request.Request(info["endpoint"], headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    agents = data.get(info["key"], 0)
                    status = "Online" if agents > 0 else "No Agents Available"
                else:
                    status = f"HTTP {response.status}"
        except urllib.error.HTTPError as e:
            status = f"HTTP Error {e.code}"
        except urllib.error.URLError as e:
            status = f"Unreachable ({e.reason})"
        except Exception as e:
            status = f"Error: {str(e)}"
            
        # Log this hour's data
        history[today_str][country][hour_str] = {
            "agents": agents,
            "status": status,
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S")
        }
        
    save_history(history)
    return history, today_str, hour_str

def generate_dashboard(history, today_str, current_hour):
    now = datetime.now()
    all_hours = [f"{h:02d}:00" for h in range(24)]
    
    # Serialize the complete history dictionary to a JSON string
    history_json_str = json.dumps(history)
    
    # Define our country sites for JS schema mapping
    sites_config = {country: {"url": info["url"]} for country, info in SITES.items()}
    sites_json_str = json.dumps(sites_config)
    hours_json_str = json.dumps(all_hours)
    
    # Define timeline headers
    timeline_headers_html = ""
    for hr in all_hours:
        timeline_headers_html += f'<th class="timeline-header">{hr.split(":")[0]}h</th>'

    # Safe HTML Template with placeholders (No f-string syntax conflict)
    html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Bosch Rexroth Country Site Monitor</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8f9fa; margin: 30px; color: #333; }
        h1 { color: #005691; border-bottom: 3px solid #005691; padding-bottom: 10px; margin-bottom: 5px; }
        .meta { color: #666; margin-bottom: 25px; font-size: 0.95em; }
        
        /* Interactive Controls */
        .controls-container { background-color: #ffffff; padding: 15px 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 25px; display: flex; align-items: center; gap: 15px; }
        .controls-container label { font-weight: bold; color: #495057; }
        .controls-container select { padding: 8px 15px; border-radius: 4px; border: 1px solid #ced4da; font-size: 1em; color: #495057; cursor: pointer; }
        .controls-container select:focus { outline: none; border-color: #005691; }

        table { width: 100%; border-collapse: collapse; background-color: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 40px; }
        th { background-color: #005691; color: white; padding: 12px 15px; font-weight: 600; text-align: left; }
        td { padding: 12px 15px; border-bottom: 1px solid #eee; }
        tr:last-child td { border-bottom: none; }
        
        .badge { padding: 5px 10px; border-radius: 20px; font-size: 0.85em; font-weight: bold; display: inline-block; }
        .badge-online { background-color: #d1e7dd; color: #0f5132; }
        .badge-no-agents { background-color: #fff3cd; color: #664d03; }
        .badge-offline { background-color: #f8d7da; color: #842029; }
        
        /* Timeline styles */
        .timeline-cell { font-size: 0.8em; text-align: center; border-left: 1px solid #f0f0f0; min-width: 35px; }
        .cell-online { background-color: #d1e7dd; color: #0f5132; }
        .cell-no-agents { background-color: #fff3cd; color: #846100; }
        .cell-offline { background-color: #f8d7da; color: #842029; }
        .cell-empty { background-color: #fafafa; color: #ccc; }
        
        .timeline-header { text-align: center; font-size: 0.75em; background-color: #f1f3f5; color: #495057; }
    </style>
    
    <script>
        // Injected data blocks safely passed via sequential replacement
        const historyData = __HISTORY_DATA__;
        const sitesConfig = __SITES_CONFIG__;
        const allHours = __ALL_HOURS__;

        function populateDateSelector() {
            const selector = document.getElementById("date-selector");
            const dates = Object.keys(historyData).sort().reverse(); // Show newest date first
            
            selector.innerHTML = "";
            dates.forEach(date => {
                const option = document.createElement("option");
                option.value = date;
                option.text = date;
                selector.appendChild(option);
            });

            if (dates.length > 0) {
                selector.selectedIndex = 0;
                renderDataForDate(dates[0]);
            }
        }

        function onDateChanged() {
            const selectedDate = document.getElementById("date-selector").value;
            renderDataForDate(selectedDate);
        }

        function renderDataForDate(selectedDate) {
            const dateData = historyData[selectedDate] || {};
            
            // 1. Render Current Site Status Table
            const statusTbody = document.getElementById("status-table-body");
            statusTbody.innerHTML = "";

            Object.keys(sitesConfig).forEach(country => {
                const config = sitesConfig[country];
                const countryToday = dateData[country] || {};
                
                // Find the latest recorded hour inside this day's log
                const loggedHours = Object.keys(countryToday).sort();
                const latestHour = loggedHours.length > 0 ? loggedHours[loggedHours.length - 1] : null;
                const latestCheck = latestHour ? countryToday[latestHour] : {"agents": -1, "status": "No logs recorded"};
                
                const agentsVal = latestCheck.agents;
                const agentsDisplay = agentsVal >= 0 ? agentsVal : "N/A";
                
                let badgeClass = "badge-offline";
                if (agentsVal > 0) {
                    badgeClass = "badge-online";
                } else if (agentsVal === 0) {
                    badgeClass = "badge-no-agents";
                }

                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td><strong>${country}</strong></td>
                    <td><a href="${config.url}" target="_blank">${config.url}</a></td>
                    <td><strong>${agentsDisplay}</strong></td>
                    <td><span class="badge ${badgeClass}">${latestCheck.status}</span></td>
                `;
                statusTbody.appendChild(tr);
            });

            // 2. Render Timeline Table
            const timelineTitle = document.getElementById("timeline-title");
            timelineTitle.innerText = `Daily Hourly Log Timeline (${selectedDate})`;

            const timelineTbody = document.getElementById("timeline-table-body");
            timelineTbody.innerHTML = "";

            Object.keys(sitesConfig).forEach(country => {
                const countryToday = dateData[country] || {};
                const tr = document.createElement("tr");
                
                let rowHtml = `<td><strong>${country}</strong></td>`;
                
                allHours.forEach(hr => {
                    if (hr in countryToday) {
                        const hourData = countryToday[hr];
                        const agents = hourData.agents;
                        if (agents > 0) {
                            rowHtml += `<td class="timeline-cell cell-online" title="${hourData.status}">${agents}a</td>`;
                        } else if (agents === 0) {
                            rowHtml += `<td class="timeline-cell cell-no-agents" title="${hourData.status}">0</td>`;
                        } else {
                            rowHtml += `<td class="timeline-cell cell-offline" title="${hourData.status}">❌</td>`;
                        }
                    } else {
                        rowHtml += `<td class="timeline-cell cell-empty">-</td>`;
                    }
                });
                
                tr.innerHTML = rowHtml;
                timelineTbody.appendChild(tr);
            });
        }

        window.onload = populateDateSelector;
    </script>
</head>
<body>
    <h1>🤖 Bosch Rexroth Chat Availability Dashboard</h1>
    <div class="meta">Last Evaluated: <strong>__LAST_CHECKED__</strong> | Check interval: Hourly</div>
    
    <!-- Interactive Date Selection Bar -->
    <div class="controls-container">
        <label for="date-selector">📅 Select Monitoring Date: </label>
        <select id="date-selector" onchange="onDateChanged()"></select>
    </div>

    <h2>Current Site Status (Last Logged Instance of Day)</h2>
    <table>
        <thead>
            <tr>
                <th>Country / Site</th>
                <th>Monitored URL</th>
                <th>Last Checked Agent Count</th>
                <th>Current Status</th>
            </tr>
        </thead>
        <tbody id="status-table-body">
            <!-- Dynamic Injection -->
        </tbody>
    </table>
    
    <h2 id="timeline-title">Daily Hourly Log Timeline</h2>
    <table>
        <thead>
            <tr>
                <th style="background-color: #495057;">Country</th>
                __TIMELINE_HEADERS__
            </tr>
        </thead>
        <tbody id="timeline-table-body">
            <!-- Dynamic Injection -->
        </tbody>
    </table>
</body>
</html>"""

    # ✅ CORRECT SEQUENTIAL REPLACEMENT CHAINING
    html = html_template.replace("__HISTORY_DATA__", history_json_str)
    html = html.replace("__SITES_CONFIG__", sites_json_str)
    html = html.replace("__ALL_HOURS__", hours_json_str)
    html = html.replace("__LAST_CHECKED__", now.strftime('%Y-%m-%d %H:%M:%S'))
    html = html.replace("__TIMELINE_HEADERS__", timeline_headers_html)

    with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
        f.write(html)
        
    print(f"[{now.strftime('%H:%M:%S')}] Interactive dashboard updated successfully.")

def btoa_obfuscate(text):
    import base64
    return base64.b64encode(text.encode()).decode()

if __name__ == "__main__":
    print("Initiating hourly check...")
    history, today, current_hour = check_availability()
    generate_dashboard(history, today, current_hour)
