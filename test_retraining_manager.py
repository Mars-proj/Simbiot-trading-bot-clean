import asyncio
import pandas as pd
from retraining_manager import RetrainingManager

async def main():
    # Create mock data
    data = pd.DataFrame({
        'close': [100 + i for i in range(1000)],
        'volume': [1000 + i for i in range(1000)]
    })
    
    # Initialize retraining manager
    retrainer = RetrainingManager("model.pth")
    
    # Run retraining
    result = await retrainer.retrain_model(data)
    print(f"Retraining result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
