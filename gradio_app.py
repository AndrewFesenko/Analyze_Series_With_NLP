import gradio as gr
import pandas as pd
import json
from theme_classifier import ThemeClassifier
from character_network import NamedEntityRecognizer, CharacterNetworkGenerator
from character_chatbot import CharacterChatBot
import os
from dotenv import load_dotenv
load_dotenv()

def get_themes(theme_list_str,subtitles_path,save_path):
    theme_list = theme_list_str.split(',')
    theme_classifier = ThemeClassifier(theme_list)
    output_df = theme_classifier.get_themes(subtitles_path,save_path)

    # Remove dialogue from the theme list
    theme_list = [theme for theme in theme_list if theme != 'dialogue']
    output_df = output_df[theme_list]

    output_df = output_df[theme_list].sum().reset_index()
    output_df.columns = ['Theme','Score']

    output_chart = gr.BarPlot(
        output_df,
        x="Theme",
        y="Score",
        title="Series Themes",
        tooltip=["Theme","Score"],
        vertical=False,
        width=500,
        height=260
    )

    return output_chart

def get_character_network(subtitles_path,ner_path):
    ner = NamedEntityRecognizer()
    ner_df = ner.get_ners(subtitles_path,ner_path)

    character_network_generator = CharacterNetworkGenerator()
    relationship_df = character_network_generator.generate_character_network(ner_df)
    html = character_network_generator.draw_network_graph(relationship_df)

    return html

# Function to load spells from the JSONL file
def load_spell_data(filepath):
    spells = []
    with open(filepath, 'r') as f:
        for line in f:
            spells.append(json.loads(line))
    return pd.DataFrame(spells)

# Load spell data
spell_data = load_spell_data('C:/Users/Andrew/Documents/AI Series/data/spell.jsonl')

def filter_spells(search_term, spell_type):
    filtered_data = spell_data

    if search_term:
        filtered_data = filtered_data[filtered_data['spell_name'].str.contains(search_term, case=False, na=False)]
    
    if spell_type and spell_type != "All":
        filtered_data = filtered_data[filtered_data['spell_type'] == spell_type]

    # Convert filtered data to an HTML table with wrapped text
    html_content = "<style>table { width: 100%; border-collapse: collapse; } th, td { padding: 8px; border: 1px solid #ddd; text-align: left; } td { word-wrap: break-word; max-width: 300px; white-space: normal; }</style>"
    html_content += "<table><tr><th>Spell Name</th><th>Spell Type</th><th>Spell Description</th></tr>"
    
    for _, row in filtered_data.iterrows():
        html_content += f"<tr><td>{row['spell_name']}</td><td>{row['spell_type']}</td><td>{row['spell_description']}</td></tr>"
    
    html_content += "</table>"
    return html_content

def chat_with_character_chatbot(message, history):
    character_chatbot = CharacterChatBot("tukyo/Clover_Llama-3.1-8B-Instruct",
                                         huggingface_token = os.getenv('huggingface_token')
                                         )

    output = character_chatbot.chat(message, history)
    output = output['content'].strip()
    return output

def main():
    with gr.Blocks() as iface:
        # Theme Classification Section
        with gr.Row():
            with gr.Column():
                gr.HTML("<h1>Theme Classification (Zero Shot Classifiers)</h1>")
                with gr.Row():
                    with gr.Column():
                        plot = gr.BarPlot()
                    with gr.Column():
                        theme_list = gr.Textbox(label="Themes")
                        subtitles_path = gr.Textbox(label="Subtitles or script Path")
                        save_path = gr.Textbox(label="Save Path")
                        get_themes_button =gr.Button("Get Themes")
                        get_themes_button.click(get_themes, inputs=[theme_list,subtitles_path,save_path], outputs=[plot])
        
        # Character Network Section
        with gr.Row():
            with gr.Column():
                gr.HTML("<h1>Character Network (NERs and Graphs)</h1>")
                with gr.Row():
                    with gr.Column():
                        network_html = gr.HTML()
                    with gr.Column():
                        subtitles_path = gr.Textbox(label="Subtitles or Script Path")
                        ner_path = gr.Textbox(label="NERs save path")
                        get_network_graph_button = gr.Button("Get Character Network")
                        get_network_graph_button.click(get_character_network, inputs=[subtitles_path,ner_path], outputs=[network_html])
                        
        # Spell Database Section
        with gr.Row():
            with gr.Column():
                spell_types = ["All"] + list(spell_data['spell_type'].unique())
                spell_type_dropdown = gr.Dropdown(label="Select Spell Type", choices=spell_types, value="All")
                search_box = gr.Textbox(label="Search Spells by Name", placeholder="Enter spell name...")
                filter_button = gr.Button("Filter Spells")
                spell_display = gr.HTML(label="Spells")  # Change to gr.HTML here

            # Update table when the button is clicked
            filter_button.click(fn=filter_spells, inputs=[search_box, spell_type_dropdown], outputs=[spell_display])

        #Character Chatbot
        with gr.Row():
            with gr.Column():
                gr.HTML("<h1>Character Chatbot</h1>")
                gr.ChatInterface(chat_with_character_chatbot)


    iface.launch(share=True)

if __name__ == '__main__':
    main()
