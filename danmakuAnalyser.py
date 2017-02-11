# coding: utf-8

import re
import jieba
import requests
from pylab import *


class Danmaku:
    
    pageString = None
    danmakuSet = []
    # 属性 p 有 8 个字段，含义分别为：
    # 1.弹幕在视频中的时间，单位为秒
    # 2.弹幕模式，1滚动弹幕 2滚动弹幕 3滚动弹幕 4底端弹幕 5顶端弹幕 6.逆向弹幕 7精准定位 8高级弹幕
    # 3.弹幕字号，字号越大字越大
    # 4.弹幕颜色
    # 5.弹幕发表时间，为时间戳
    # 6.弹幕池，0普通池 1字幕池 2特殊池
    # 7.弹幕发送者ID
    # 8.弹幕在B站数据库中的真实ID
    
    
    def __init__(self, av, p):
        try:
            biliUrl = 'http://www.bilibili.com/video/av{0}/'.format(av)
            if(int(p) > 1):
                biliUrl += 'index_{0}.html'.format(p)
            biliPage = requests.get(biliUrl).text

            cid_reg = '(?<=cid\=)\d*'
            cid = None
            if re.search(cid_reg, biliPage) == None:
                raise DAError('invalid av or p')
            else:
                cid = re.search(cid_reg, biliPage).group()

            danmakuUrl = 'http://comment.bilibili.com/{0}.xml'.format(cid)
            danmakuPage = requests.get(danmakuUrl).text
        except DAError as e:
            print('出现异常。', e.value)
            exit()

        self.pageString = danmakuPage
        danmakuList = danmakuPage.split('\r\n')
        danmakuList[0] = re.sub('.*<d', '<d', danmakuList[0]) # 第一行为一些元数据+第一条记录，把前面的元数据去掉
        danmakuInfo = []
        for elem in range(len(danmakuList)):
            try:
                danmakuParams = danmakuList[elem].split('"')[1].split(',')
                danmakuText = [re.sub('<[^>]+>', '', danmakuList[elem])]
                danmakuText.extend(danmakuParams)
                danmakuInfo.append(danmakuText)
            except:
                continue
        self.danmakuSet = danmakuInfo


    def countDanmakuBySecond(self, limit = 0):
        danmakuTime = {}
        for elem in self.danmakuSet:
            danmakuSecond = float(elem[1])
            if str(math.floor(danmakuSecond)) in danmakuTime.keys():
                danmakuTime[str(math.floor(danmakuSecond))] += 1
            else:
                danmakuTime[str(math.floor(danmakuSecond))] = 1
        sortedDanmakuTime = sorted(danmakuTime.items(), key = lambda item:item[1])[::-1]
        if limit == 0:
            return sortedDanmakuTime
        else:
            return sortedDanmakuTime[:limit]


    def countWordFrequency(self, limit = 10):
        wordFrequency = {}
        seperator = '|'
        for elem in self.danmakuSet:
            segment = seperator.join(jieba.cut(elem[0]))
            seg_split = segment.split(seperator)
            for part in seg_split:
                if part in wordFrequency.keys():
                    wordFrequency[part] += 1
                else:
                    wordFrequency[part] = 1
        wordDicSorted = sorted(wordFrequency.items(), key = lambda item:item[1])[::-1]
        cutWordFrequency = []
        ret = 0
        pointer = 0
        while 1:
            if len(wordDicSorted[pointer][0]) > 1:
                cutWordFrequency.append(wordDicSorted[pointer])
                ret += 1
                if ret == limit:
                    break
                pointer += 1
            else:
                pointer += 1
                continue
        return cutWordFrequency


class Graph:

    def printGraphBySecond(self, danmaku):
        # 每秒弹幕数
        secondList = danmaku.countDanmakuBySecond()
        xkeys = []
        for elem in range(len(secondList)):
            secondList[elem] = list(secondList[elem])
            secondList[elem][0] = int(secondList[elem][0])
            xkeys.append(int(secondList[elem][0]))
        for i in range(max(xkeys) + 1):
            if i not in xkeys:
                secondList.append([i, 0])
        secondList = sorted(secondList)
        xData = []
        yData = []
        for elem in secondList:
            xData.append(int(elem[0]))
            yData.append(elem[1])
        #plt.plot(xData, yData)
        #plt.fill_between(xData, yData)
        plt.xlabel('时间（秒）')
        plt.ylabel('弹幕数（条）')
        plt.bar(xData, yData, 1, label = '总弹幕数({0})'.format(len(danmaku.danmakuSet)))
        # 关键词出现次数
        frequencyLimit = 3
        lineColors = ['red', 'green', 'yellow', 'cyan', 'magenta']
        colorNum = 0
        keywords = danmaku.countWordFrequency(frequencyLimit)[::-1]
        for keyword in keywords:
            wordFrequency = Util.wordFrequencyInDanmaku(keyword[0], danmaku)
            wordFrequency = sorted(wordFrequency.items(), key=lambda item: item[1])
            xkeys = []
            for elem in range(len(wordFrequency)):
                wordFrequency[elem] = list(wordFrequency[elem])
                wordFrequency[elem][0] = int(wordFrequency[elem][0])
                xkeys.append(int(wordFrequency[elem][0]))
            for i in range(max(xkeys) + 1):
                if i not in xkeys:
                    wordFrequency.append([i, 0])
            wordFrequency = sorted(wordFrequency)
            xData = []
            yData = []
            for elem in wordFrequency:
                xData.append(int(elem[0]))
                yData.append(elem[1])
            plt.plot(xData, yData, color = lineColors[colorNum], label = '{0}({1})'.format(keyword[0], keyword[1]))
            colorNum += 1
        plt.legend()
        plt.show()


class DAError(Exception):

    def __init__(self, value):
        if value == 'invalid av or p':
            self.value = '检查av号或p数是否正确。'

class Util:
    # 多维数组按某一个维度排序
    @staticmethod
    def listSortByDimension(ndlist, dimension):
        ndlist.sort(key=lambda x:x[dimension])

    # 秒数转换为 mm:ss 格式时间
    @staticmethod
    def second2Minute(seconds):
        sec = seconds % 60
        min = int((seconds - sec) / 60)
        return str(min).zfill(2) + ':' + str(sec).zfill(2)

    # mm:ss 格式时间转换为秒数
    @staticmethod
    def minute2Second(minutes):
        parts = minutes.split(':')
        sec = int(parts[0]) * 60 + int(parts[1])
        return sec

    # 计算某个词语在每秒中出现次数
    @staticmethod
    def wordFrequencyInDanmaku(keyword, danmaku):
        frequency = {}
        for elem in danmaku.danmakuSet:
            if str(math.floor(float(elem[1]))) not in frequency.keys():
                frequency[str(math.floor(float(elem[1])))] = 0
            if elem[0].count(keyword) > 0:
                frequency[str(math.floor(float(elem[1])))] += elem[0].count(keyword)
        return frequency

if __name__ == '__main__':
    avId = input('输入av号：\n')
    partId = input('输入p数，若只有1p输入1：\n')

    mpl.rcParams['font.sans-serif'] = ['Microsoft YaHei']

    dmk = Danmaku(avId, partId)
    gr = Graph()
    gr.printGraphBySecond(dmk)