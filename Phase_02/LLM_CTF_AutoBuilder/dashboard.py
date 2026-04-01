"""
CTF AutoBuilder - Web管理界面
运行: python dashboard.py
访问: http://localhost:5001
"""
from flask import Flask, jsonify, render_template_string
import sqlite3
import os

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ctf_tasks.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

HTML = '''
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LLM CTF AutoBuilder - 管理面板</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: "Microsoft YaHei", sans-serif; background: #0d1117; color: #c9d1d9; }
  
  .header {
    background: linear-gradient(135deg, #161b22 0%, #1f2937 100%);
    border-bottom: 1px solid #30363d;
    padding: 20px 30px;
    display: flex;
    align-items: center;
    gap: 15px;
  }
  .header h1 { font-size: 22px; color: #58a6ff; }
  .header .subtitle { font-size: 13px; color: #8b949e; margin-top: 4px; }
  .badge {
    background: #1f6feb;
    color: #fff;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 12px;
    margin-left: auto;
  }

  .container { padding: 24px 30px; max-width: 1400px; margin: 0 auto; }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 24px;
  }
  .stat-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 20px;
    text-align: center;
  }
  .stat-card .number { font-size: 36px; font-weight: bold; color: #58a6ff; }
  .stat-card .label { font-size: 13px; color: #8b949e; margin-top: 6px; }
  .stat-card.success .number { color: #3fb950; }
  .stat-card.failed .number { color: #f85149; }
  .stat-card.rate .number { color: #d29922; }

  .charts-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 24px;
  }
  .chart-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 20px;
  }
  .chart-card h3 { font-size: 14px; color: #8b949e; margin-bottom: 16px; }

  .table-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 24px;
  }
  .table-card h3 { font-size: 14px; color: #8b949e; margin-bottom: 16px; }
  
  .filter-bar {
    display: flex;
    gap: 10px;
    margin-bottom: 16px;
    flex-wrap: wrap;
  }
  .filter-bar select, .filter-bar input {
    background: #0d1117;
    border: 1px solid #30363d;
    color: #c9d1d9;
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 13px;
  }
  .filter-bar button {
    background: #1f6feb;
    color: #fff;
    border: none;
    padding: 6px 16px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 13px;
  }

  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th { text-align: left; padding: 10px 12px; color: #8b949e; border-bottom: 1px solid #30363d; font-weight: 500; }
  td { padding: 10px 12px; border-bottom: 1px solid #21262d; }
  tr:hover td { background: #1c2128; }
  
  .status-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 500;
  }
  .status-success { background: #0d4429; color: #3fb950; border: 1px solid #238636; }
  .status-failed  { background: #3d1f1f; color: #f85149; border: 1px solid #da3633; }
  .status-pending { background: #2d2a1f; color: #d29922; border: 1px solid #9e6a03; }

  .cat-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
  }
  .cat-web     { background: #0d2d6b; color: #58a6ff; }
  .cat-pwn     { background: #3d1a1a; color: #f85149; }
  .cat-crypto  { background: #1a2d1a; color: #3fb950; }
  .cat-misc    { background: #2d1f0d; color: #d29922; }
  .cat-reverse { background: #1f0d2d; color: #bc8cff; }
  .cat-db      { background: #0d2d2d; color: #79c0ff; }

  .diff-badge {
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 4px;
  }
  .diff-easy   { background: #0d4429; color: #3fb950; }
  .diff-medium { background: #2d2a1f; color: #d29922; }
  .diff-hard   { background: #3d1f1f; color: #f85149; }

  .refresh-btn {
    float: right;
    background: #21262d;
    color: #c9d1d9;
    border: 1px solid #30363d;
    padding: 6px 14px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 13px;
  }
  .refresh-btn:hover { background: #30363d; }

  .flag-cell { font-family: monospace; font-size: 12px; color: #3fb950; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .task-id-cell { font-family: monospace; font-size: 11px; color: #8b949e; }
</style>
</head>
<body>

<div class="header">
  <div>
    <h1>🚩 LLM CTF AutoBuilder</h1>
    <div class="subtitle">基于大语言模型的CTF题目智能生成系统 · 管理面板</div>
  </div>
  <span class="badge" id="last-update">加载中...</span>
</div>

<div class="container">
  
  <!-- 统计卡片 -->
  <div class="stats-grid">
    <div class="stat-card">
      <div class="number" id="total-count">-</div>
      <div class="label">总生成题目</div>
    </div>
    <div class="stat-card success">
      <div class="number" id="success-count">-</div>
      <div class="label">成功上线</div>
    </div>
    <div class="stat-card failed">
      <div class="number" id="failed-count">-</div>
      <div class="label">生成失败</div>
    </div>
    <div class="stat-card rate">
      <div class="number" id="success-rate">-%</div>
      <div class="label">生成成功率</div>
    </div>
  </div>

  <!-- 图表 -->
  <div class="charts-grid">
    <div class="chart-card">
      <h3>📊 题型分布</h3>
      <canvas id="categoryChart" height="200"></canvas>
    </div>
    <div class="chart-card">
      <h3>📈 难度分布</h3>
      <canvas id="difficultyChart" height="200"></canvas>
    </div>
  </div>

  <!-- 题目列表 -->
  <div class="table-card">
    <h3>📋 题目记录
      <button class="refresh-btn" onclick="loadData()">🔄 刷新</button>
    </h3>
    <div class="filter-bar">
      <select id="filter-category" onchange="filterTable()">
        <option value="">所有类型</option>
        <option value="web">Web</option>
        <option value="pwn">Pwn</option>
        <option value="crypto">Crypto</option>
        <option value="misc">Misc</option>
        <option value="reverse">Reverse</option>
        <option value="db">Database</option>
      </select>
      <select id="filter-difficulty" onchange="filterTable()">
        <option value="">所有难度</option>
        <option value="easy">简单</option>
        <option value="medium">中等</option>
        <option value="hard">困难</option>
      </select>
      <select id="filter-status" onchange="filterTable()">
        <option value="">所有状态</option>
        <option value="success">成功</option>
        <option value="failed">失败</option>
        <option value="pending">待定</option>
      </select>
    </div>
    <table id="tasks-table">
      <thead>
        <tr>
          <th>任务ID</th>
          <th>题目名称</th>
          <th>类型</th>
          <th>难度</th>
          <th>状态</th>
          <th>Flag</th>
          <th>端口</th>
          <th>生成时间</th>
        </tr>
      </thead>
      <tbody id="tasks-tbody">
        <tr><td colspan="8" style="text-align:center;color:#8b949e;padding:40px">加载中...</td></tr>
      </tbody>
    </table>
  </div>

</div>

<script>
function getStatusLabel(s) {
  if (s === 'success') return '✅ 成功';
  if (s === 'failed')  return '❌ 失败';
  if (s === 'pending') return '⏳ 待定';
  return s;
}
let allTasks = [];
let categoryChart, difficultyChart;

async function loadData() {
  const resp = await fetch('/api/stats');
  const data = await resp.json();
  
  // 更新统计
  document.getElementById('total-count').textContent = data.total;
  document.getElementById('success-count').textContent = data.success;
  document.getElementById('failed-count').textContent = data.failed;
  document.getElementById('success-rate').textContent = data.rate + '%';
  document.getElementById('last-update').textContent = '最后更新: ' + new Date().toLocaleTimeString();

  // 更新图表
  updateCategoryChart(data.by_category);
  updateDifficultyChart(data.by_difficulty);

  // 更新表格
  allTasks = data.tasks;
  filterTable();
}

function updateCategoryChart(data) {
  const ctx = document.getElementById('categoryChart').getContext('2d');
  if (categoryChart) categoryChart.destroy();
  categoryChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: Object.keys(data),
      datasets: [{
        data: Object.values(data),
        backgroundColor: ['#1f6feb','#da3633','#238636','#9e6a03','#6e40c9','#1f7a8c'],
        borderWidth: 0
      }]
    },
    options: {
      plugins: { legend: { labels: { color: '#c9d1d9', font: { size: 12 } } } }
    }
  });
}

function updateDifficultyChart(data) {
  const ctx = document.getElementById('difficultyChart').getContext('2d');
  if (difficultyChart) difficultyChart.destroy();
  difficultyChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: Object.keys(data),
      datasets: [{
        label: '题目数量',
        data: Object.values(data),
        backgroundColor: ['#238636','#9e6a03','#da3633'],
        borderRadius: 4
      }]
    },
    options: {
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: '#8b949e' }, grid: { color: '#21262d' } },
        y: { ticks: { color: '#8b949e', stepSize: 1 }, grid: { color: '#21262d' } }
      }
    }
  });
}

function filterTable() {
  const cat  = document.getElementById('filter-category').value;
  const diff = document.getElementById('filter-difficulty').value;
  const stat = document.getElementById('filter-status').value;

  const filtered = allTasks.filter(t =>
    (!cat  || t.category  === cat)  &&
    (!diff || t.difficulty === diff) &&
    (!stat || t.status    === stat)
  );

  const tbody = document.getElementById('tasks-tbody');
  if (filtered.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:#8b949e;padding:40px">暂无记录</td></tr>';
    return;
  }

  tbody.innerHTML = filtered.map(t => `
    <tr>
      <td class="task-id-cell">${t.task_id}</td>
      <td>${t.title || '-'}</td>
      <td><span class="cat-badge cat-${t.category}">${t.category || '-'}</span></td>
      <td><span class="diff-badge diff-${t.difficulty}">${t.difficulty || '-'}</span></td>
      <td><span class="status-badge status-${t.status}">${getStatusLabel(t.status)}</span></td>
      <td class="flag-cell" title="${t.flag}">${t.flag || '-'}</td>
      <td>${t.port || '-'}</td>
      <td>${t.created_at || '-'}</td>
    </tr>
  `).join('');
}

// 自动刷新
loadData();
setInterval(loadData, 30000);
</script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/api/stats')
def stats():
    conn = get_db()
    
    tasks = conn.execute(
        'SELECT task_id, title, category, difficulty, status, flag, port, created_at FROM tasks ORDER BY created_at DESC'
    ).fetchall()
    
    total   = len(tasks)
    success = sum(1 for t in tasks if t['status'] == 'success')
    failed  = sum(1 for t in tasks if t['status'] == 'failed')
    rate    = round(success / total * 100, 1) if total > 0 else 0
    
    by_category   = {}
    by_difficulty = {}
    for t in tasks:
        if t['status'] == 'success':
            cat  = t['category']  or 'unknown'
            diff = t['difficulty'] or 'unknown'
            by_category[cat]   = by_category.get(cat, 0)   + 1
            by_difficulty[diff] = by_difficulty.get(diff, 0) + 1
    
    conn.close()
    return jsonify({
        'total':         total,
        'success':       success,
        'failed':        failed,
        'rate':          rate,
        'by_category':   by_category,
        'by_difficulty': by_difficulty,
        'tasks':         [dict(t) for t in tasks]
    })

if __name__ == '__main__':
    print("🚀 CTF AutoBuilder 管理面板启动中...")
    print("📊 访问地址: http://localhost:5001")
    app.run(host='0.0.0.0', port=5001, debug=False)
