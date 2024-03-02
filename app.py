from flask import Flask, render_template, request, jsonify, url_for
import os, config
from flask_cors import CORS
from openai import OpenAI
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)


api_key = config.OPENAI_API_KEY
if not api_key:
    raise ValueError("The OPENAI_API_KEY environment variable must be set.")
client = OpenAI(api_key=api_key)


@app.route('/')
def index():
    return render_template('index2.html')


@app.route('/synthesize', methods=['POST'])
def synthesize_text():
    data = request.json
    # print(data)  # 查看接收到的数据
    text= data.get('text')

    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    target_language = data.get('targetLang')  # 前端需要发送这个信息

    # 声音选择逻辑
    voice_map = {
        'en': 'en-US-JennyNeural',
        'cn': 'zh-CN-YunyangNeural',
        'fi': 'fi-FI-HarriNeural',
        'fr': 'fr-FR-HenriNeural',
        'ja': 'ja-JP-NanamiNeural',
        'is': 'is-IS-GunnarNeural'
    }
    # 根据目标语言选择声音，如果没有匹配的语言，默认使用英语声音
    voice_name = voice_map.get(target_language, 'en-US-JennyNeural')


    speech_config = speechsdk.SpeechConfig(subscription=config.synthesize_key, region=config.region)
    # For web app, we don't use the default speaker but rather generate an audio file
    audio_config = speechsdk.audio.AudioOutputConfig(filename="static/target_speech.wav")
    speech_config.speech_synthesis_voice_name= voice_name
    
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    speech_synthesis_result = speech_synthesizer.speak_text_async(text).get()
    
    if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("Speech synthesized for text [{}]".format(text))
        # Return the path to the synthesized audio file
        return jsonify({'message': 'Synthesis completed', 'audio_path': url_for('static', filename='target_speech.wav')})

    elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_synthesis_result.cancellation_details
        error_message = "Speech synthesis canceled: {}".format(cancellation_details.reason)
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            if cancellation_details.error_details:
                error_message += "\nError details: {}".format(cancellation_details.error_details)
        return jsonify({'error': error_message}), 500
    

@app.route('/synthesize_s', methods=['POST']) #source text speak
def synthesize_source():
    data = request.json
    # print(data)  # 查看接收到的数据
    text= data.get('text')
    print(text)

    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    source_language = data.get('sourceLang')  # 前端需要发送这个信息

    # 声音选择逻辑
    voice_map = {
        'en': 'en-US-JennyNeural',
        'cn': 'zh-CN-YunyangNeural',
        'fi': 'fi-FI-HarriNeural',
        'fr': 'fr-FR-HenriNeural',
        'ja': 'ja-JP-NanamiNeural',
        'is': 'is-IS-GunnarNeural'
    }
    # 根据目标语言选择声音，如果没有匹配的语言，默认使用英语声音
    voice_name = voice_map.get(source_language, 'en-US-JennyNeural')


    speech_config = speechsdk.SpeechConfig(subscription=config.synthesize_key, region=config.region)
    # For web app, we don't use the default speaker but rather generate an audio file
    audio_config = speechsdk.audio.AudioOutputConfig(filename="static/source_speech.wav")
    speech_config.speech_synthesis_voice_name= voice_name
    
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    speech_synthesis_result = speech_synthesizer.speak_text_async(text).get()
    
    if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("Speech synthesized for text [{}]".format(text))
        # Return the path to the synthesized audio file
        return jsonify({'message': 'Synthesis completed', 'audio_path': url_for('static', filename='source_speech.wav')})

    elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_synthesis_result.cancellation_details
        error_message = "Speech synthesis canceled: {}".format(cancellation_details.reason)
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            if cancellation_details.error_details:
                error_message += "\nError details: {}".format(cancellation_details.error_details)
        return jsonify({'error': error_message}), 500

@app.route('/translate', methods=['POST'])
def translate():
    # Extracting data from POST request
    data = request.json
    source_text = data['text']
    source_language = data['sourceLang']
    target_language = data['targetLang']

    # Constructing the message for translation
    # Adjust the prompt as needed for your translation task
    prompt = f"Please ignore all previous instructions. Please respond only in the {target_language} language.\
      Do not explain what you are doing. Do not self reference. You are an expert translator. \
      Just give me the answer of the translation, no other words\
      Translate the following text from {source_language} to the {target_language} using vocabulary \
      and expressions of a native {target_language} speaker.Translate the following text : '{source_text}'."


    # Make an API call to OpenAI's Chat Completions
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a native translator."},
                {"role": "user", "content": prompt}
            ]
        )

        # Extracting the assistant's message from the response
        translated_text = response.choices[0].message.content
        translated_text = translated_text.replace('"', '')
        # print(response.choices[0].message.content)
        return jsonify(translated_text=translated_text)

    except Exception as e:
        # Handling exceptions and errors
        print(f"An error occurred: {e}")
        return jsonify(error=str(e)), 500

@app.route('/explain', methods=['POST'])
def explain():
    # 获取 POST 请求中的数据
    data = request.json
    text_to_explain = data['to_explain']
    source_language = data['sourceLang']
    explain_language = data['exLang']


    prompt = f"Explain the following {source_language} sentence: '{text_to_explain}' with grammar and vocubularies in {explain_language}, \
        your audience can only understand {explain_language} and a native {explain_language} speaker, \
                so make sure to expain everything only in {explain_language}."
    
    # 调用 ChatGPT API 进行解释
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", 
            messages=[
                {"role": "system", "content": "You are a language teacher."},
                {"role": "user", "content": prompt}
            ]
        )

        explanation = response.choices[0].message.content
        return jsonify(explanation=explanation)

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify(error=str(e)), 500

if __name__ == '__main__':
    app.run(debug=True)
