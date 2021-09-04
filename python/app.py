#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import json
import logging
import requests

from flask import Flask, abort, request

from xiaoai import (XiaoAIAudioItem, XiaoAIDirective, XiaoAIOpenResponse,
                    XiaoAIResponse, XiaoAIStream, XiaoAIToSpeak, XiaoAITTSItem,
                    xiaoai_request, xiaoai_response)


serviceURL = 'https://dev.hellocraft.xyz/node/'

def build_text_message(to_speak, is_session_end, open_mic):
    xiao_ai_response = XiaoAIResponse(
        to_speak=XiaoAIToSpeak(type_=0, text=to_speak),
        open_mic=open_mic)
    response = xiaoai_response(XiaoAIOpenResponse(version='1.0',
                                                  is_session_end=is_session_end,
                                                  response=xiao_ai_response))
    return response


def build_music_message(to_speak, mp3_urls):
    all_list = []
    if to_speak is not None:
        info_tts = XiaoAIDirective(
            type_='tts',
            tts_item=XiaoAITTSItem(
                type_='0', text=to_speak
            ))

        all_list.append(info_tts)
    place_holder = XiaoAIDirective(
            type_='audio',
            audio_item=XiaoAIAudioItem(stream=XiaoAIStream(url='https://just.a/placeholder.mp3'))
        )
    all_list.append(place_holder)
    for url in mp3_urls:
        info_audio = XiaoAIDirective(
            type_='audio',
            audio_item=XiaoAIAudioItem(stream=XiaoAIStream(url=url))
        )
        all_list.append(info_audio)
    xiao_ai_response = XiaoAIResponse(directives=all_list, open_mic=False)
    response = xiaoai_response(XiaoAIOpenResponse(
        version='1.0', is_session_end=True, response=xiao_ai_response))
    return response

def build_single_music_msg(to_speak,attributes_data):
    all_list = []
    if to_speak is not None:
        info_tts = XiaoAIDirective(
            type_='tts',
            tts_item=XiaoAITTSItem(
                type_='0', text=to_speak
            ))

        # all_list.append(info_tts)
    currentSongPos = attributes_data['currentSongPos']
    songUrl = attributes_data['songIdList'][currentSongPos]
    info_audio = XiaoAIDirective(
        type_='audio',
        audio_item=XiaoAIAudioItem(stream=XiaoAIStream(url=songUrl))
    )
    for num in range(1,40):
        all_list.append(info_audio)
    xiao_ai_response = XiaoAIResponse(directives=all_list, open_mic=False, register_events=[{"event_name":"mediaplayer.playbacknearlyfinished"}])
    response = xiaoai_response(XiaoAIOpenResponse(
        version='1.0', session_attributes=attributes_data, is_session_end=True, response=xiao_ai_response))
    return response

def get_favorites_single(attributes_data):
    if attributes_data is None:
        mp3_urls = json.loads(requests.get(
            serviceURL + '/likelist').text)['result']
        attributes_data = {'songListStartFrom':0}
        attributes_data['currentSongPos'] = 0
        attributes_data['alreadyPlayed'] = 0
        attributes_data['songIdList'] = mp3_urls
        return build_single_music_msg('马上开始播放收藏歌单',attributes_data)
    elif attributes_data['alreadyPlayed'] - attributes_data['songListStartFrom'] >= 40:
        mp3_urls = json.loads(requests.get(
            serviceURL + '/likelist?startFrom=' + (attributes_data['songListStartFrom'] + 40)).text)['result']
        attributes_data['songListStartFrom'] = attributes_data['songListStartFrom'] + 40
        attributes_data['currentSongPos'] = 0 
        attributes_data['songIdList'] = mp3_urls
    attributes_data['alreadyPlayed'] = attributes_data['alreadyPlayed'] + 1

    return build_single_music_msg(None,attributes_data)

def get_favorites():
    # 获取（部分）红心歌曲列表
    mp3_urls = json.loads(requests.get(
        serviceURL + '/likelist').text)['result']

    # 顺序播放红心歌曲
    return build_music_message('马上播放收藏歌曲', mp3_urls)


def get_random_favorites():
    # 随机获取（部分）红心歌曲列表
    mp3_urls = json.loads(requests.get(
        serviceURL + '/random_likelist').text)['result']

    # 随机播放顺序播放红心歌曲
    return build_music_message('马上乱序播放收藏歌曲', mp3_urls)


def get_recommendation():
    # 获取每日推荐列表
    mp3_urls = json.loads(requests.get(
        serviceURL + '/recommend').text)['result']

    # 顺序播放每日推荐歌曲
    return build_music_message('马上播放每日推荐', mp3_urls)

def get_random_recommended_list():
    # 随机获取每日推荐歌单
    from random import shuffle
    result = json.loads(requests.get(
        serviceURL + '/random_recommended_list').text)
    mp3_urls = result['result']
    name = result['name']
    shuffle(mp3_urls)

    # 随机播放每日推荐歌曲
    return build_music_message('马上播放推荐歌单 ' + name, mp3_urls)

def get_random_recommendation():
    # 随机获取每日推荐列表
    from random import shuffle
    mp3_urls = json.loads(requests.get(
        serviceURL + '/recommend').text)['result']
    shuffle(mp3_urls)

    # 随机播放每日推荐歌曲
    return build_music_message('马上乱序播放每日推荐', mp3_urls)


def parse_input(event):
    req = xiaoai_request(event)
    if req.request.type == 0:
        # 技能进入请求
        if req.request.slot_info.intent_name == 'Favorites':
            return get_favorites()
        elif req.request.slot_info.intent_name == 'Recommendation':
            return get_random_recommendation()     
        elif req.request.slot_info.intent_name == 'Ramdom_Recommended_List':
            return get_random_recommended_list()
        else:
            return build_text_message('好的，已打开网易云音乐', is_session_end=False, open_mic=True)
    elif req.request.type == 1:
        if req.request.event_type == 'mediaplayer.playbacknearlyfinished':
            return get_favorites_single(json.loads(req.session.attributes))
        # Issue: http://www.miui.com/thread-21675179-1-1.html
        elif req.request.slot_info.intent_name == 'Favorites':
            if '随机' in req.query:
                return get_random_favorites()
            elif '单曲' in req.query:
                return get_favorites_single(None)
            else:
                return get_favorites()
        elif req.request.slot_info.intent_name == 'Recommendation':
            return get_recommendation()
        elif req.request.slot_info.intent_name == 'Ramdom_Favorites':
            return get_random_favorites()
        elif req.request.slot_info.intent_name == 'Ramdom_Recommendation':
            return get_random_recommendation()
        elif req.request.slot_info.intent_name == 'Ramdom_Recommended_List':
            return get_random_recommended_list()
        elif req.request.slot_info.intent_name == 'Mi_Exit':
            return build_text_message('再见了您！', is_session_end=True, open_mic=False)
        else:
            return build_text_message('你可以说：收藏', is_session_end=False, open_mic=True)
    elif req.request.type == 2:
        return build_text_message('再见了您！', is_session_end=True, open_mic=False)
    else:
        return build_text_message('我没听懂欸', is_session_end=True, open_mic=False)


app = Flask(__name__)
logging.basicConfig(filename='myapp.log', level=logging.INFO)


@app.route('/xiaoai', methods=['POST'])
def index():
    if not request.json:
        abort(400)
    logging.info('Input = ' + str(request.json))
    response = parse_input(request.json)
    logging.info('Response = ' + str(response))
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3002, debug=True)
