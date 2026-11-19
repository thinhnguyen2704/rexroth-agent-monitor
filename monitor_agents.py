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
    today_data = history.get(today_str, {})
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Bosch Rexroth Country Site Monitor</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8f9fa; margin: 30px; color: #333; }}
        h1 {{ color: #005691; border-bottom: 3px solid #005691; padding-bottom: 10px; margin-bottom: 5px; }}
        .meta {{ color: #666; margin-bottom: 30px; font-size: 0.95em; }}
        table {{ width: 100%; border-collapse: collapse; background-color: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 40px; }}
        th {{ background-color: #005691; color: white; padding: 12px 15px; font-weight: 600; text-align: left; }}
        td {{ padding: 12px 15px; border-bottom: 1px solid #eee; }}
        tr:last-child td {{ border-bottom: none; }}
        .badge {{ padding: 5px 10px; border-radius: 20px; font-size: 0.85em; font-weight: bold; display: inline-block; }}
        .badge-online {{ background-color: #d1e7dd; color: #0f5132; }}
        .badge-no-agents {{ background-color: #fff3cd; color: #664d03; }}
        .badge-offline {{ background-color: #f8d7da; color: #842029; }}
        
        /* Timeline styles */
        .timeline-cell {{ font-size: 0.8em; text-align: center; border-left: 1px solid #f0f0f0; min-width: 35px; }}
        .cell-online {{ background-color: #d1e7dd; color: #0f5132; }}
        .cell-no-agents {{ background-color: #fff3cd; color: #846100; }}
        .cell-offline {{ background-color: #f8d7da; color: #842029; }}
        .cell-empty {{ background-color: #fafafa; color: #ccc; }}
        
        .timeline-header {{ text-align: center; font-size: 0.75em; background-color: #f1f3f5; color: #495057; }}
    </style>
</head>
<body>
    <h1>🤖 Bosch Rexroth Chat Availability</h1>
    <div class="meta">Last System Check: <strong>{now.strftime('%Y-%m-%d %H:%M:%S')}</strong> | Check interval: Hourly</div>
    
    <h2>Current Site Status</h2>
    <table>
        <thead>
            <tr>
                <th>Country / Site</th>
                <th>Monitored URL</th>
                <th>Last Checked Agent Count</th>
                <th>Current Status</th>
            </tr>
        </thead>
        <tbody>
    """
    
    for country, info in SITES.items():
        # Get latest checked record
        country_today = today_data.get(country, {})
        latest_check = country_today.get(current_hour, {"agents": -1, "status": "Not Checked Yet"})
        
        agents_val = latest_check["agents"]
        agents_display = str(agents_val) if agents_val >= 0 else "N/A"
        
        if agents_val > 0:
            badge_class = "badge-online"
        elif agents_val == 0:
            badge_class = "badge-no-agents"
        else:
            badge_class = "badge-offline"
            
        html += f"""
            <tr>
                <td><strong>{country}</strong></td>
                <td><a href="{info['url']}" target="_blank">{info['url']}</a></td>
                <td><strong>{agents_display}</strong></td>
                <td><span class="badge {badge_class}">{latest_check['status']}</span></td>
            </tr>
        """
        
    html += """
        </tbody>
    </table>
    
    <h2>Daily Hourly Log Timeline ({})</h2>
    <table>
        <thead>
            <tr>
                <th style="background-color: #495057;">Country</th>
    """.format(today_str)
    
    for hr in all_hours:
        html += f'<th class="timeline-header">{hr.split(":")[0]}h</th>'
        
    html += """
            </tr>
        </thead>
        <tbody>
    """
    
    for country in SITES.keys():
        html += f"<tr><td><strong>{country}</strong></td>"
        country_today = today_data.get(country, {})
        
        for hr in all_hours:
            if hr in country_today:
                hour_data = country_today[hr]
                agents = hour_data["agents"]
                if agents > 0:
                    html += f'<td class="timeline-cell cell-online" title="{hour_data["status"]}">{agents}a</td>'
                elif agents == 0:
                    html += f'<td class="timeline-cell cell-no-agents" title="{hour_data["status"]}">0</td>'
                else:
                    html += f'<td class="timeline-cell cell-offline" title="{hour_data["status"]}">❌</td>'
            else:
                html += '<td class="timeline-cell cell-empty">-</td>'
        html += "</tr>"
        
    html += """
        </tbody>
    </table>
</body>
</html>
    """
    
    with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[{now.strftime('%H:%M:%S')}] Dashboard updated successfully: {DASHBOARD_FILE}")

if __name__ == "__main__":
    print("Initiating hourly check...")
    history, today, current_hour = check_availability()
    generate_dashboard(history, today, current_hour)
