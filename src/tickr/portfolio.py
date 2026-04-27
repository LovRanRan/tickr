"""Portfolio class — Stage 3.

OOP showcase. Will hold a list[PortfolioEntry] and implement at least:
- __repr__   → "Portfolio(<n> holdings, total=$X)"
- __len__    → number of holdings
- __iter__   → iterate over PortfolioEntry instances
- __add__    → merge two portfolios (sum quantities for shared symbols)

classmethod:
- from_json(cls, path) — load a Portfolio from disk
"""
import json
from pathlib import Path
from tickr.models import PortfolioEntry 

class Portfolio:
    def __init__(self, entries: list[PortfolioEntry] | None = None):
        self.entries = list(entries) if entries else []
    def __repr__(self) -> str:
        symbols = ", ".join(e.symbol for e in self.entries)
        return f"Portfolio({len(self.entries)} holdings: {symbols})"
    def __len__(self) -> int:
        return len(self.entries)
    def __iter__(self):
        return iter(self.entries)
    def __add__(self, other: "Portfolio") -> "Portfolio":
    # 用 dict 临时聚合,key 是 symbol
        merged: dict[str, PortfolioEntry] = {}
        
        for entry in list(self.entries) + list(other.entries):
            if entry.symbol in merged:
                # 已存在,合并 quantity 和 avg_cost
                existing = merged[entry.symbol]
                new_qty = existing.quantity + entry.quantity
                new_avg = _weighted_avg(existing, entry)  # 自己写一个 helper
                merged[entry.symbol] = PortfolioEntry(
                    symbol=entry.symbol,
                    quantity=new_qty,
                    avg_cost=new_avg,
                )
            else:
                merged[entry.symbol] = entry
        
        return Portfolio(list(merged.values()))
    def save_json(self, path: str | Path) -> None:
        """Serialize this Portfolio to a JSON file."""
        data = [e.model_dump() for e in self.entries]
        json_str = json.dumps(data, indent=2)
        Path(path).write_text(json_str)

    @classmethod
    def from_json(cls, path: str | Path) -> "Portfolio":
        """Load a Portfolio from a JSON file."""
        text = Path(path).read_text()                                   # 1. 读
        data = json.loads(text)                                          # 2. JSON 字符串 → list[dict]
        entries = [PortfolioEntry.model_validate(d) for d in data]      # 3. dict → PortfolioEntry
        return cls(entries) 
    
def _weighted_avg(a: PortfolioEntry, b: PortfolioEntry) -> float | None:
    """Cost-weighted average of two entries' avg_cost. None if neither has it."""
    if a.avg_cost is not None and b.avg_cost is not None:
        return (a.quantity * a.avg_cost + b.quantity * b.avg_cost) / (a.quantity + b.quantity)
    
    # 情况 2: 只有一个有 → 用有的那个
    if a.avg_cost is not None:
        return a.avg_cost
    if b.avg_cost is not None:
        return b.avg_cost
    
    # 情况 3: 两个都没有
    return None