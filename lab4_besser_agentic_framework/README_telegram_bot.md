

---

# Telegram Plotting Bot
Telegram bot can help you get Python plotting code given some instructions. You can do histograms, bar plots, line plots.
If providing only the plot type it will ask follow-up questions to clarify missing information such as axis labels or data values.

---

## Features

- Understands natural language plot requests (e.g., "plot a bar chart of sales by region").
- Extracts plot type, axis labels, and values from user input.
- Asks follow-up questions if information is missing.
- Generates ready-to-run Python code using `matplotlib` and `pandas`.
- Supports flexible phrasing and conversational flow.

---

## Supported Plot Types

- Histogram  
- Bar Plot  
- Line Plot  

---

## Supported Input Formats

### Plot Type Detection
The first interaction with the bot is requesting a plot to be built. For example,
- "I want a histogram"  
- "Draw a bar chart"  
- "Make a line plot"  

### Axis Label Extraction
If the user just requests a plot type, a follow up question regarding the axis albels will be asked, which can be answered:
- "x is age, y is glasses"  
- "plot glasses vs age"  
- "glasses by age"  
- "age on x, glasses on y"  

### Value Input
In case there is not details about x axis or y axis plot values, you can provide it when prompted by the follow up question:
- "A, B, C, D" → for x-axis values  
- "10, 20, 15, 30" → for y-axis values  

---

## Conversation Flow

Example:

```
User: Plot a bar chart of sales by region  
Bot: What are the values for the x-axis (region)?  
User: North, South, East, West  
Bot: Now provide the values for the y-axis (sales).  
User: 100, 150, 90, 120  
Bot: Returns Python code for the plot  
```

---

## Setup Instructions
Have the basics installed: `besser-2.6.1`,  `besser-agentic-framework-3.0.1`
Configure `config.ini` with a Telegram bot token.
Run the bot with:```python smart_agent.py```

---

## File Structure

```
telegram_plot_bot/
├── smart_agent.py                # Main bot logic
├── config.ini            # Telegram bot token and settings
└── README_telegram_bot.md             # This file
```

---

## Notes

- The bot uses spaCy for natural language processing.
- I encountered errors with `nltk` module beacause `punkt_tab` was not being downloaded. That was caused because of an issue with SSL certificate. The solution was that I disabled the SSL certificate verification and ran `nltk.download('nltk_tab')` manually. 


