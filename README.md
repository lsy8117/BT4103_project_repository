# Capstone_Project

This template should help get you started developing with Vue 3 in Vite.

## Recommended IDE Setup

[VSCode](https://code.visualstudio.com/) + [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur).

## Customize configuration

See [Vite Configuration Reference](https://vitejs.dev/config/).

## Project Setup

```sh
npm install
```

### Compile and Hot-Reload for Development

```sh
npm run dev
```

### Compile and Minify for Production

```sh
npm run build
```

## List of Routers

- **MatrixFactorizationRouter ("mf")**  
  Uses a matrix factorization model trained on the preference data (recommended).  
  *Requires OpenAI API key*  
  Utilizes OpenAI embedding model.

- **SWRankingRouter ("sw_ranking")**  
  Uses a weighted Elo calculation for routing, where each vote is weighted according to how similar it is to the user's prompt.  
  *Requires OpenAI API key*  
  Utilizes OpenAI embedding model.

- **CausalLLMRouter ("causal_llm")**  
  Uses a LLM-based classifier tuned on the preference data.  
  *Requires Nvidia GPU*

- **BERTRouter ("bert")**  
  Uses a BERT classifier trained on the preference data.

- **RandomRouter ("random")**  
  Randomly routes to either model.

---

## Calibration of Router Threshold

### Step 1: Install the required package

Install the `routellm[serve,eval]` python package:

```sh
pip install "routellm[serve,eval]"
```

### Step 2: Import the necessary modules
```sh
import os
os.environ["OPENAI_API_KEY"] = "sk-xxxxx" # Do not need to be real OpenAI api key if you are not calibrating "mf" or "sw_ranking"

from datasets import Dataset, load_dataset
from pandarallel import pandarallel
from routellm.controller import Controller
```

### Step 3: Set environment variables
```sh
dataset = "lmsys/lmsys-arena-human-preference-55k" # Huggingface dataset for calibration (you can use your own dataset with the same format)

percentage_of_calls_to_stronger_model = 0.5 # % of calls routed to the strong model

routers = ["mf","sw_ranking","causal_llm","bert","random"] # List of routers for calibration

strong_model = "gemini/gemini-flash" # Strong model
weak_model = "ollama_chat/seeyssimon/bt4103_gguf_finance" # Weak model
```

### Step 4: Calibrate thresholds
```sh
pandarallel.initialize(progress_bar=True)
dataset_df = load_dataset(dataset, split="train").to_pandas()
dataset_df = dataset_df[0:50]  # Remove this line for real use case

controller = Controller(
    routers=routers,
    config=None,
    progress_bar=True,
    strong_model=strong_model,
    weak_model=weak_model,
)

# Calculate win rates and thresholds for each router
for router in routers:
    win_rates = controller.batch_calculate_win_rate(dataset_df["prompt"], router)
    dataset_df[str(router)] = win_rates

for router in routers:
    threshold = dataset_df[router].quantile(q=1 - percentage_of_calls_to_stronger_model)
    print(f"For {percentage_of_calls_to_stronger_model * 100}% strong model calls for {router}, threshold = {round(threshold, 5)}")
```

### Example output
```sh
For 50.0% strong model calls for bert, threshold = 0.62427
```
This means that the threshold should be set to `0.62427` for the BERT router so that approximately 50% of calls are routed to the strong model i.e. using a model field of router-bert-0.62427.
Update the `.env` file with the following:
```sh
ROUTER_THRESHOLD = '0.62427'
ROUTER_MODEL = 'bert'
```
