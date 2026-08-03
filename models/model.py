from dataclasses import dataclass
from typing import List
import pandas as pd


@dataclass
class PrimaryProduct:
    name: str
    stage1_time: float  # Processing time for Stage 1 (min)
    stage1_profit: float  # Profit generated at Stage 1


class SharedStage2Pipeline:

    def __init__(
        self,
        stage2_time: float = 460,
        stage2_profit: float = 4581,  # Kept at 4581
        day_minutes: float = 1440,
    ):
        self.stage2_time = stage2_time
        self.stage2_profit = stage2_profit
        self.day_minutes = day_minutes

    def evaluate_products(
        self, products: List[PrimaryProduct]
    ) -> pd.DataFrame:
        rows = []

        for p in products:
            # 1. Stage 1 Metrics
            s1_rate = p.stage1_profit / p.stage1_time
            s1_daily_profit = (self.day_minutes / p.stage1_time) * p.stage1_profit

            # 2. Stage 2 Metrics
            # Note: If stage2_profit represents total profit (4581) rather than incremental extra profit,
            # incremental profit added in Stage 2 is (stage2_profit - stage1_profit) = 472.
            s2_incremental_profit = self.stage2_profit - p.stage1_profit
            s2_rate = s2_incremental_profit / self.stage2_time

            # Stage 2 Daily Profit calculation using overall profit (4581) across combined processing time
            s2_daily_profit = (
                self.day_minutes / (p.stage1_time + self.stage2_time)
            ) * self.stage2_profit

            # Decision Rule: Compare actual Daily Profit outputs directly
            run_stage2 = s2_daily_profit > s1_daily_profit

            rows.append(
                {
                    "Product": p.name,
                    "Stage 1 Profit": p.stage1_profit,
                    "Stage 1 Rate ($/min)": round(s1_rate, 2),
                    "Stage 2 Rate ($/min)": round(s2_rate, 2),
                    "Stage 1 Daily Profit": round(s1_daily_profit, 2),
                    "Stage 2 Daily Profit": round(s2_daily_profit, 2),
                    "Optimal Decision": "Run Stage 2"
                    if run_stage2
                    else "Stop at Stage 1",
                }
            )

        return pd.DataFrame(rows)


# --- Example Simulation ---
products_list = [
    PrimaryProduct(
        name="Product A (AL Base)", stage1_time=691, stage1_profit=4109
    )
]

# Pipeline instance with stage2_profit = 4581
pipeline = SharedStage2Pipeline(stage2_time=460, stage2_profit=4581)
df_results = pipeline.evaluate_products(products_list)

print("=== EVALUATION TABLE ===")
print(df_results.to_string(index=False))