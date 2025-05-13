import logging
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, ApplicationBuilder, MessageHandler, filters

import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

from besser.agent.core.agent import Agent
from besser.agent.core.session import Session
from besser.agent.exceptions.logger import logger
# Configure the logging module (optional)
logger.setLevel(logging.INFO)

# Create the agent
agent = Agent('telegram_agent')
agent.load_properties('config.ini')

# Define the platform your agent will use
telegram_platform = agent.use_telegram_platform()

# Adding a custom handler for the Telegram Application: command /help
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = agent.get_or_create_session(str(update.effective_chat.id), telegram_platform)
    session.reply('I can help with plotting instructions. Please provide details.')

help_handler = CommandHandler('help', help)
telegram_platform.add_handler(help_handler)

import spacy
# Load the English NLP model
nlp = spacy.load("en_core_web_sm")

# Function to generate plot code based on keywords
def extract_plot_type(instruction):
        instruction = instruction.lower()
        if any(word in instruction for word in ['histogram', 'hist']):
            return """
            import pandas as pd
            import matplotlib.pyplot as plt

            # Example data
            data = {'values': [1, 2, 2, 3, 3, 3, 4, 4, 4, 4]}
            df = pd.DataFrame(data)

            df['values'].plot(kind='hist', bins=5)
            plt.xlabel('Value')
            plt.ylabel('Frequency')
            plt.title('Histogram')
            plt.show()
            """
        elif any(word in instruction for word in ['bar plot', 'bar chart', 'bar']):
            return """
            import pandas as pd
            import matplotlib.pyplot as plt

            # Example data
            data = {'categories': ['A', 'B', 'C', 'D'], 'values': [4, 7, 1, 8]}
            df = pd.DataFrame(data)

            df.plot(kind='bar', x='categories', y='values')
            plt.xlabel('Category')
            plt.ylabel('Value')
            plt.title('Bar Plot')
            plt.show()
            """
        elif any(word in instruction for word in ['line plot', 'line chart', 'line']):
            return """
            import pandas as pd
            import matplotlib.pyplot as plt

            # Example data
            data = {'x': [1, 2, 3, 4, 5], 'y': [2, 3, 5, 7, 11]}
            df = pd.DataFrame(data)

            df.plot(kind='line', x='x', y='y')
            plt.xlabel('X-axis label')
            plt.ylabel('Y-axis label')
            plt.title('Line Plot')
            plt.show()
            """
        else:
            return None


def extract_axis_labels(instruction):
    doc = nlp(instruction.lower())

    # Filter out common filler words and phrases
    ignore_words = {'i', 'want', 'a', 'an', 'the', 'plot', 'chart', 'graph', 'with', 'show', 'display', 'draw', 'make', 'create', 'of', 'by', 'to'}
    nouns = [token.text for token in doc if token.pos_ in ['NOUN', 'PROPN'] and token.text not in ignore_words]

    if len(nouns) >= 2:
        return nouns[0], nouns[1]  # x, y
    elif len(nouns) == 1:
        return nouns[0], None
    else:
        return None, None


def generate_plot_code(instruction):
    plot_type = extract_plot_type(instruction)
    x_label, y_label = extract_axis_labels(instruction)

    if not plot_type:
        return "What type of plot would you like? (e.g., histogram, bar plot, line plot)"

    if not x_label or not y_label:
        return "What should be on the x-axis and y-axis? Please provide a sample or description."

    return f"""
import pandas as pd
import matplotlib.pyplot as plt

# Sample data
data = {{
    '{x_label}': ['A', 'B', 'C', 'D'],
    '{y_label}': [10, 20, 15, 30]
}}
df = pd.DataFrame(data)

df.plot(kind='{plot_type.split()[0]}', x='{x_label}', y='{y_label}')
plt.xlabel('{x_label.capitalize()}')
plt.ylabel('{y_label.capitalize()}')
plt.title('{plot_type.capitalize()}')
plt.show()
"""

# Function to generate and send plot code as text
async def generate_and_send_plot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    instruction = update.message.text
    plot_code = generate_plot_code(instruction)
    if "Sorry" in plot_code:
        await update.message.reply_text(plot_code)
    else:
        await update.message.reply_text(f"Here is the code for your plot:\n\n{plot_code}")

# Adding a custom handler for plot instructions
plot_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), generate_and_send_plot)
telegram_platform.add_handler(plot_handler)

# STATES
initial_state = agent.new_state('initial_state', initial=True)
awaiting_state = agent.new_state('awaiting_state')
plotting_state = agent.new_state('plotting_state')
plotting_type_state = agent.new_state('plotting_type_state')

# INTENTS
help_intent = agent.new_intent('help_intent', [
    'help',
    '/help'
])

plot_intent = agent.new_intent('plot_intent', [
    'plot',
    'graph',
    'chart',
])

plot_type_intent = agent.new_intent('plot_type_intent', [
    'histogram',
    'bar plot',
    'line plot'
])

# STATES BODIES' DEFINITION + TRANSITIONS
def initial_body(session: Session):
    session.reply('Hi! I am here to chat with you. How can I assist you today?')

def awaiting_body(session: Session):
    session.reply('I can help with plotting instructions. Please provide details.')


def generate_custom_plot_code(plot_type, x_label, y_label):
    return f"""
import pandas as pd
import matplotlib.pyplot as plt

# Sample data
data = {{
    '{x_label}': ['A', 'B', 'C', 'D'],
    '{y_label}': [10, 20, 15, 30]
}}
df = pd.DataFrame(data)

df.plot(kind='{plot_type.split()[0]}', x='{x_label}', y='{y_label}')
plt.xlabel('{x_label.capitalize()}')
plt.ylabel('{y_label.capitalize()}')
plt.title('{plot_type.capitalize()}')
plt.show()
"""
import re

def extract_axis_labels_from_response(text):
    text = text.lower().strip()

    # Pattern 1: x = ..., y = ...
    x_match = re.search(r"x\s*(=|is|:)?\s*([\w\s]+)", text)
    y_match = re.search(r"y\s*(=|is|:)?\s*([\w\s]+)", text)
    if x_match and y_match:
        return x_match.group(2).strip(), y_match.group(2).strip()

    # Pattern 2: ... vs ...
    if " vs " in text:
        parts = text.split(" vs ")
        if len(parts) == 2:
            return parts[1].strip(), parts[0].strip()  # x, y

    # Pattern 3: ... by ...
    if " by " in text:
        parts = text.split(" by ")
        if len(parts) == 2:
            return parts[1].strip(), parts[0].strip()  # x, y

    # Pattern 4: ... on x, ... on y
    x_match = re.search(r"on x\s*(=|is|:)?\s*([\w\s]+)", text)
    y_match = re.search(r"on y\s*(=|is|:)?\s*([\w\s]+)", text)
    if x_match and y_match:
        return x_match.group(2).strip(), y_match.group(2).strip()

    return None, None

def generate_custom_plot_code_with_values(plot_type, x_label, y_label, x_values, y_values):
    return f"""
import pandas as pd
import matplotlib.pyplot as plt

# Custom data
data = {{
    '{x_label}': {x_values},
    '{y_label}': {y_values}
}}
df = pd.DataFrame(data)

df.plot(kind='{plot_type.split()[0]}', x='{x_label}', y='{y_label}')
plt.xlabel('{x_label.capitalize()}')
plt.ylabel('{y_label.capitalize()}')
plt.title('{plot_type.capitalize()}')
plt.show()
"""

def plotting_body(session: Session):
    instruction = session.event.message

    # Step 1: Handle axis label clarification
    if session.get('awaiting_axis_labels'):
        x_label, y_label = extract_axis_labels_from_response(instruction)
        if x_label and y_label:
            session.set('x_label', x_label)
            session.set('y_label', y_label)
            session.delete('awaiting_axis_labels')
            session.set('awaiting_x_values', True)
            session.reply(f"Great! What are the values for the x-axis ({x_label})? Please separate them with commas.")
        else:
            session.reply("Please specify both x and y axis labels, like: `x is age, y is glasses`.")
        return

    # Step 2: Handle x-values input
    if session.get('awaiting_x_values'):
        x_values = [v.strip() for v in instruction.split(',')]
        session.set('x_values', x_values)
        session.delete('awaiting_x_values')
        session.set('awaiting_y_values', True)
        y_label = session.get('y_label')
        session.reply(f"Thanks! Now provide the values for the y-axis ({y_label}). Please separate them with commas.")
        return

    # Step 3: Handle y-values input
    if session.get('awaiting_y_values'):
        try:
            y_values = [float(v.strip()) for v in instruction.split(',')]
        except ValueError:
            session.reply("Please make sure all y-axis values are numbers, separated by commas.")
            return

        session.set('y_values', y_values)
        session.delete('awaiting_y_values')

        # Generate the plot code
        plot_type = session.get('plot_type')
        x_label = session.get('x_label')
        y_label = session.get('y_label')
        x_values = session.get('x_values')

        plot_code = generate_custom_plot_code_with_values(plot_type, x_label, y_label, x_values, y_values)
        session.reply("Here is the code for your custom plot:")
        session.reply(f"```python\n{plot_code}\n```")
        return

    # Step 4: First message — extract plot type and labels
    plot_type = extract_plot_type(instruction)
    x_label, y_label = extract_axis_labels(instruction)

    if not plot_type:
        session.reply("What type of plot would you like? (e.g., histogram, bar plot, line plot)")
        return

    if not x_label or not y_label:
        session.set('plot_type', plot_type)
        session.set('awaiting_axis_labels', True)
        session.reply("What should be on the x-axis and y-axis? Please describe or give an example.")
        return

    # Ask for x-values
    session.set('plot_type', plot_type)
    session.set('x_label', x_label)
    session.set('y_label', y_label)
    session.set('awaiting_x_values', True)
    session.reply(f"What are the values for the x-axis ({x_label})? Please separate them with commas.")


initial_state.set_body(initial_body)
initial_state.when_intent_matched(help_intent).go_to(awaiting_state)
initial_state.when_intent_matched(plot_intent).go_to(plotting_state)
initial_state.when_intent_matched(plot_type_intent).go_to(plotting_type_state)

awaiting_state.set_body(awaiting_body)
awaiting_state.when_intent_matched(plot_intent).go_to(plotting_state)
awaiting_state.when_intent_matched(plot_type_intent).go_to(plotting_type_state)

plotting_state.set_body(plotting_body)
plotting_type_state.set_body(plotting_body)
plotting_type_state.when_no_intent_matched().go_to(plotting_state)
plotting_state.when_no_intent_matched().go_to(plotting_state)
plotting_state.when_intent_matched(plot_intent).go_to(plotting_state)
plotting_type_state.when_intent_matched(plot_type_intent).go_to(plotting_type_state)

# RUN APPLICATION
if __name__ == '__main__':
    agent.run()
