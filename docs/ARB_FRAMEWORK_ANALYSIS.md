# hzjken/crypto-arbitrage-framework - Analysis & Integration

## Overview

**Repository:** https://github.com/hzjken/crypto-arbitrage-framework  
**Language:** Python  
**Key Libraries:** ccxt, docplex (CPLEX solver), numpy  
**License:** Not specified (check repo)

---

## Core Innovation: Two-Step LP Optimization

Unlike brute-force arbitrage bots, this framework uses **Linear Programming** to find optimal paths:

### Step 1: PathOptimizer
```
INPUT: Market prices from multiple exchanges (via CCXT)
↓
MODEL: Linear programming with CPLEX solver
↓
OUTPUT: Arbitrage path that maximizes rate of return
       (not just "any profitable path" - the OPTIMAL path)
```

**Key Features:**
- **No length limit** on arbitrage path (multi-lateral, not just triangular)
- **Considers fees** (trading fees, withdrawal fees, commissions)
- **Balance constraints** - only paths feasible with current balance
- **Inter-exchange balance constraints** - cross-platform transfers need confirmed balance
- **CPLEX solver** is MUCH faster than brute-force enumeration

### Step 2: AmtOptimizer
```
INPUT: Optimal path from PathOptimizer + Orderbook data
↓
MODEL: Mixed-integer linear programming
↓
OUTPUT: Optimal trading amount for EACH step in the path,
        considering orderbook depth, price levels, and precision
```

**Key Features:**
- **Orderbook-aware** - looks at top N price levels
- **Precision constraints** - respects exchange decimal requirements
- **Volume limits** - only trades what's available in orderbook
- **Balance continuity** - each step's input = previous step's output

---

## Architecture Components

### 1. PathOptimizer (path_optimizer.py)
```
Key Decision Variables:
- x[i,j] = binary, whether path goes from currency i to j
- transit_price_matrix[i,j] = transfer rate from i to j
- commission_matrix[i,j] = fee for trading i→j

Key Constraints:
- Path must be closed (starts and ends same currency)
- Max path length limit
- Must start from currency with balance > 0
- Inter-exchange transfers need withdrawal fee estimation

Objective: Maximize total return rate
```

### 2. AmtOptimizer (amount_optimizer.py)
```
Key Decision Variables:
- x[i,j] = integer, trading amount at price level j in step i
- y[i,j] = binary, whether price level j is chosen for step i
- z[i,j] = real, actual trading amount = x * precision

Key Constraints:
- Only one price level per step
- Amount ≤ orderbook volume at that level
- Balance continuity through path
- Minimum trading limit ($10 USD)

Objective: Maximize total profit
```

### 3. TradeExecutor (trade_execution.py)
```
Key Features:
- Multi-threading: parallel execution on same exchange
- Sequential: inter-exchange trades (needs blockchain confirmation)
- Timeout mechanism: cancel order if not filled in 30s
- Kucoin special handling: main/trading account transfers

Execution Flow:
1. Assign trades to threads (intra-exchange = parallel, inter-exchange = sequential)
2. Execute with wait_and_cancel logic
3. If any trade fails → cancel subsequent trades
```

---

## Key Differentiators from Other Arbitrage Bots

| Feature | This Framework | Typical Arbitrage Bots |
|---------|---------------|----------------------|
| Path Finding | LP Optimization (CPLEX) | Brute force enumeration |
| Path Length | Unlimited (multi-lateral) | Max 3 (triangular) |
| Amount Optimization | Orderbook-aware LP | Fixed amounts |
| Execution | Multi-threaded + timeout | Sequential |
| Fee Handling | Comprehensive (withdrawal, trading, spread) | Simple fee model |
| Balance Constraints | Real balance awareness | Often ignored |

---

## Integration into KEOTrading

### What We Take (Adapt/Import)

1. **Path Optimization Logic**
   - Replace CPLEX with open-source alternative (PULP + CBC solver)
   - Same LP model structure
   - Much faster than our current brute-force approach

2. **Amount Optimization Algorithm**
   - Orderbook depth consideration
   - Multi-level price discovery
   - Precision handling per exchange

3. **Trade Execution Pattern**
   - Multi-threading for parallel orders
   - Timeout + cancel mechanism
   - Inter-exchange sequential execution

### What We Improve

| Original | KEOTrading Improvement |
|----------|----------------------|
| CPLEX (commercial, needs license) | PULP + CBC (MIT, open-source) |
| Single-threaded monitoring | 50 agents with Redis pub/sub |
| No risk management layer | Full risk enforcement |
| No dashboard | Full control center |
| Static path length | Dynamic per-agent specialization |

---

## Open Source Alternative to CPLEX

CPLEX is commercial (IBM). We use **PULP + CBC** instead:

```python
from pulp import *

# Same LP structure, open-source solver
model = LpProblem("Arbitrage", LpMaximize)
x = LpVariable.dicts("edge", edges, cat="Binary")
# ... same constraints ...
model.solve(PULP_CBC_CMD())
# or for larger problems:
# model.solve(CPLEX_CMD())
```

**PULP** is a Python wrapper that supports:
- CBC (Coin-OR Branch and Cut) - default, open-source
- CPLEX - if you have a license
- GLPK - GNU Linear Programming Kit
- SCIP - open-source

---

## Code Snippets to Integrate

### Path Optimizer (Adapted)
```python
from pulp import LpProblem, LpMaximize, LpVariable, LpBinary, lpSum, value
from itertools import combinations

class ArbitragePathOptimizer:
    """
    Multi-lateral arbitrage path optimizer using LP.
    Finds the profit-maximizing closed trading path.
    """
    
    def __init__(self, exchanges, config):
        self.exchanges = exchanges
        self.config = config
        self.currency_set = set()
        self.price_data = {}
        
    def find_arbitrage(self):
        """
        Run LP to find optimal arbitrage path.
        Returns: (profit_rate, path) or (0, None)
        """
        # Build price matrix from all exchanges
        self._fetch_all_prices()
        
        # Build LP model
        model = LpProblem("Arbitrage", LpMaximize)
        
        # Decision variables: which edges to use
        edges = self._get_all_edges()
        x = LpVariable.dicts("x", edges, cat=LpBinary)
        
        # Objective: maximize return rate
        returns = {e: self._get_return_rate(e) for e in edges}
        model += lpSum(returns[e] * x[e] for e in edges)
        
        # Constraints
        # 1. Flow conservation (except start/end)
        for c in self.currency_set:
            in_edges = [(i,j) for (i,j) in edges if j == c]
            out_edges = [(i,j) for (i,j) in edges if i == c]
            if in_edges and out_edges:
                model += lpSum(x[i,j] for i,j in in_edges) == lpSum(x[i,j] for i,j in out_edges)
        
        # 2. Path length limit
        model += lpSum(x[e] for e in edges) <= self.config.max_path_length
        
        # 3. Path must be closed (start = end currency)
        # ... (additional constraints)
        
        # Solve
        model.solve(PULP_CBC_CMD(msg=0))
        
        if value(model.objective) > 1 + self.config.min_profit_rate:
            path = self._extract_path(x)
            return value(model.objective) - 1, path
        return 0, None
    
    def _fetch_all_prices(self):
        """Parallel fetch from all exchanges via CCXT"""
        from utils import multiThread
        # Fetch and merge price data
        pass
    
    def _get_return_rate(self, edge):
        """Calculate net return rate after fees"""
        exc, pair, direction = self._parse_edge(edge)
        price = self.price_data[exc][pair]['bid' if direction == 'sell' else 'ask']
        fee = self.exchanges[exc].fees['trade']['maker']
        return (1 - fee) * price if direction == 'sell' else (1 - fee) / price
```

### Amount Optimizer (Adapted)
```python
class AmountOptimizer:
    """
    Optimizes trading amounts for a given arbitrage path,
    considering orderbook depth and price levels.
    """
    
    def __init__(self, path, exchanges, config):
        self.path = path
        self.exchanges = exchanges
        self.config = config
        self.orderbook_depth = 10  # top N levels
        
    def optimize_amounts(self):
        """
        Mixed-integer LP to find optimal amounts per step.
        Returns: dict of {step: {amount, price, direction}}
        """
        model = LpProblem("AmountOptim", LpMaximize)
        
        steps = len(self.path)
        
        # Amount variables (integer - to handle precision)
        amount = LpVariable.dicts("amt", 
                                  [(i,j) for i in range(steps) for j in range(self.orderbook_depth)],
                                  lowBound=0)
        
        # Selection variables (binary - which price level)
        select = LpVariable.dicts("sel",
                                  [(i,j) for i in range(steps) for j in range(self.orderbook_depth)],
                                  cat=LpBinary)
        
        # Objective: maximize profit
        model += lpSum(self._get_profit(i, j) * amount[i,j] * select[i,j] 
                      for i in range(steps) for j in range(self.orderbook_depth))
        
        # Constraints
        # 1. Only one price level per step
        for i in range(steps):
            model += lpSum(select[i,j] for j in range(self.orderbook_depth)) == 1
        
        # 2. Amount ≤ volume at selected level
        for i in range(steps):
            for j in range(self.orderbook_depth):
                model += amount[i,j] <= self.volume[i,j] * select[i,j]
        
        # 3. Balance continuity
        # ... (balance flow constraints)
        
        # 4. Minimum trade value
        # ... (min USD value constraints)
        
        model.solve(PULP_CBC_CMD(msg=0))
        
        return self._extract_solution(amount, select)
```

---

## Execution Integration

```python
class ArbitrageExecutor:
    """
    Executes arbitrage trades with multi-threading and timeout.
    """
    
    def __init__(self, exchanges):
        self.exchanges = exchanges
        self.order_timeout = 30  # seconds
        
    def execute(self, path, amounts):
        """
        Execute arbitrage path with given amounts.
        Returns: success boolean
        """
        # Group by exchange (intra-exchange = parallel)
        tasks = self._group_tasks(path, amounts)
        
        # Execute intra-exchange trades in parallel
        results = multiThread(self._execute_intra_exchange, 
                             tasks['intra'], 
                             len(tasks['intra']))
        
        # If any failed, cancel all
        if not all(results):
            self._cancel_pending(tasks)
            return False
        
        # Execute inter-exchange sequentially (blockchain time)
        for trade in tasks['inter']:
            if not self._execute_inter_exchange(trade):
                return False
        
        return True
    
    def _execute_intra_exchange(self, exchange, trades):
        """Execute all trades on one exchange in parallel"""
        results = []
        for trade in trades:
            order = exchange.create_limit_order(...)
            # Wait with timeout
            if not self._wait_for_fill(order, exchange):
                return False
            results.append(True)
        return all(results)
    
    def _wait_for_fill(self, order, exchange):
        """Wait for order fill with timeout"""
        start = time.time()
        while time.time() - start < self.order_timeout:
            status = exchange.fetch_order(order['id'])
            if status == 'closed':
                return True
            time.sleep(0.2)
        exchange.cancel_order(order['id'])
        return False
```

---

## Summary: What We Integrate

| Component | Integration Method |
|-----------|------------------|
| LP-based path finding | New module `src/strategies/arbitrage/lp_optimizer.py` |
| Amount optimization | Extend existing execution agents |
| Orderbook analysis | New data agent type |
| Multi-threading execution | Integrate into execution layer |
| Fee modeling | Extend risk/config components |

---

## Advantages Over Current KEOTrading Arbitrage

1. **Faster** - LP vs brute force enumeration
2. **Global optimum** - maximizes profit, not just "any profit"
3. **Multi-lateral** - paths of any length, not just triangular
4. **Realistic execution** - orderbook-aware amounts, not theoretical
5. **Open-source solver** - PULP/CBC, no commercial license needed

---

## References

- [PULP Documentation](https://coin-or.github.io/pulp/)
- [CBC Solver](https://github.com/coin-or/Cbc)
- [CCXT Library](https://github.com/ccxt/ccxt)
- [Original Framework](https://github.com/hzjken/crypto-arbitrage-framework)
