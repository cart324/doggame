import discord
from discord.ext import commands
import random
import time

client = discord.Bot(intents=discord.Intents.all())

current_card = ""
seat = 0
answers = []
user_list = []
respond_user = []
user_dict = {}
score_dict = {}
win_score = 0
vote_user = []
analects_dict = {}
all_opportunity = []
after_open = False
started = False
wait = False
choice = False
scaffolded = False
banned = False

with open("card.txt", "r", encoding='UTF8') as cards:
    card_list = []
    for card in cards:
        card_list.append(card)

with open("respond.txt", "r", encoding='UTF8') as samples:
    sample_list = []
    for sample in samples:
        sample_list.append(sample)

now = str(time.strftime('%Y.%m.%d %H:%M:%S - '))
print(now + "Data load complete (Info: There is no additional log system yet)")


def next_round():
    global user_list
    global respond_user
    global answers
    first = user_list[0]
    user_list = user_list[1:]
    user_list.append(first)
    respond_user = []
    answers = []


def score_up(user_id):
    global score_dict
    user_score = score_dict.get(user_id)
    user_score += 1
    score_dict[user_id] = user_score


def clear_db():
    global started
    global user_list
    global respond_user
    global answers
    global score_dict
    started = False
    user_list = []
    respond_user = []
    answers = []
    score_dict = {}


def analact_append(user_number):
    full_answer = ""
    win_user = respond_user[user_number]
    for answer in answers[user_number]:
        full_answer = current_card.replace("_____", f"**__{answer}__**", 1)
    analects = analects_dict.get(win_user)
    analects.append(full_answer)
    analects_dict[win_user] = analects


@client.command(guild_ids=[907936221446148138])
async def join(ctx):
    global user_list
    if started is True:
        await ctx.respond("게임이 이미 시작되었습니다.")
    elif ctx.author.id in user_list:
        await ctx.respond("이미 등록한 유저입니다.", ephemeral=True)
    else:
        user_id = ctx.author.id
        user_name = ctx.author.name
        user_list.append([user_id, user_name])
        await ctx.respond("성공적으로 등록되었습니다.")


@client.command(guild_ids=[907936221446148138])
async def start(ctx, score: discord.Option(int), open_user: discord.Option(str, choices=["답변자 공개", "답변자 미공개"]),
                update_reward_for_universe: discord.Option(str, choices=["준다", "안준다"])):
    global started
    global win_score
    global after_open
    global all_opportunity
    win_score = score
    started = True
    random.shuffle(user_list)
    text = ""
    if open_user == "답변자 공개":
        after_open = True
        text = "\n(답변자가 공개되는 설정입니다.)"
    elif open_user == "답변자 미공개":
        after_open = False
    for user in user_list:
        user_dict[user[0]] = user[1]
        score_dict[user[0]] = 0
        analects_dict[user[0]] = []
        all_opportunity.append(user[0])
    if 278170182227066880 in user_list and update_reward_for_universe == "준다":
        score_dict[278170182227066880] = 3
        text = text + "\n유니를 위한 업데이트 사료 3.24점이 제공되었습니다!(청약철회는 받지 않습니다.)"
    await ctx.respond("우승점수 " + str(win_score) + "점으로 게임이 시작되었습니다.\n첫 술래는 " + user_list[0][1] + "입니다." + text)


@client.command(guild_ids=[907936221446148138])
async def end(ctx):
    global choice
    choice = False
    clear_db()
    await ctx.respond("게임이 종료되었습니다.")


@client.command(guild_ids=[907936221446148138])
async def score(ctx):
    scores = score_dict.items()
    new_score = []
    texts = f"우승 점수 : {win_score}\n"
    for each_score in scores:
        new_score.append([user_dict.get(each_score[0]), each_score[1]])
    new_score.sort(key=lambda x: -x[1])  # 1번 인덱스를 기준으로 역순 정렬
    for text in new_score:
        texts = texts + text[0] + " : " + str(text[1]) + "점\n"
    await ctx.respond(texts)


@client.command(guild_ids=[907936221446148138])
async def draw(ctx):
    global seat
    global wait
    global choice
    global current_card
    if ctx.author.id is not user_list[0][0]:
        await ctx.respond("당신의 차례가 아닙니다.", ephemeral=True)
    else:
        if choice is True:
            await ctx.respond("choice를 먼저 해주세요.", ephemeral=True)
        else:
            current_card = random.choice(card_list)
            seat = current_card.count("_")
            current_card = current_card.replace("_", "_____")
            wait = True
            choice = True
            await ctx.respond("`" + current_card + "`")


@client.command(guild_ids=[907936221446148138])
async def submit(ctx, first, second, third):
    global answers
    global wait
    global respond_user
    global vote_user
    global scaffolded
    if wait is False or ctx.author.id == user_list[0][0]:
        await ctx.respond("당신의 차례가 아닙니다.", ephemeral=True)
    elif ctx.author.id in respond_user:
        await ctx.respond("이미 응답하였습니다.", ephemeral=True)
    else:
        reply = [first, second, third]
        answers.append(reply[:seat])
        respond_user.append(ctx.author.id)
        await ctx.send(str(len(respond_user)) + "명이 응답하였습니다. (" + str(len(user_list)-len(respond_user)-1) + "명 남음)")
        if len(answers) == len(user_list) - 1:
            vote_user = []
            scaffolded = False
            wait = False
            all_answer = f"문장 : {current_card}\n{user_list[0][1]}가 고릅니다.\n"
            count = 1
            for answer in answers:
                answer_text = ", ".join(map(str, answer))
                all_answer = all_answer + f"{count}번 유저 : " + answer_text + "\n"
                count += 1
            await ctx.send("```" + all_answer + "```")
        await ctx.respond("응답이 기록되었습니다.", ephemeral=True)


@client.command(guild_ids=[907936221446148138])
async def choice(ctx, number: discord.Option(int)):
    global choice
    if number > len(respond_user) or number < 1:
        await ctx.respond("ERROR다 멍청아", ephemeral=True)
    elif ctx.author.id is not user_list[0][0]:
        await ctx.respond("당신의 차례가 아닙니다.", ephemeral=True)
    else:
        number -= 1
        win_user = respond_user[number]
        score_up(win_user)
        choice = False
        if after_open:
            text = ""
            user_number = 0
            for x in respond_user:
                user_number += 1
                text = text + str(user_number) + "번 유저는 " + user_dict.get(x) + "\n"
            text = "```" + text + "였습니다!```"
            await ctx.send(text)
        analact_append(number)
        if score_dict.get(win_user) >= win_score:
            clear_db()
            analects = analects_dict.get(win_user)
            text = ">>> "
            for analect in analects:
                text = text + "" + analect + "\n"
            message_id = await ctx.send("@everyone 우승자 " + user_dict.get(win_user) + "의 어록 모음집\n" + text, silent=True)
            pin_id = await ctx.pins(message_id)
            await ctx.delete(pin_id)
            await ctx.respond(str(number + 1) + "번 유저 " + user_dict.get(win_user) +
                              "가 최종 우승입니다! 우리의 새로운 멍멍이를 위해 축하해주세요!")
        else:
            next_round()
            await ctx.respond(str(number + 1) + "번 유저 " + user_dict.get(win_user) + "가 우승하였습니다!\n다음 술래는 " + user_list[0][1] + "입니다.")


@client.command(guild_ids=[907936221446148138])
async def choice_all(ctx):
    global all_opportunity
    global choice
    if ctx.author.id is not user_list[0][0]:
        await ctx.respond("당신의 차례가 아닙니다.", ephemeral=True)
    else:
        if user_list[0][1] not in all_opportunity:
            await ctx.respond("이미 기회를 소진하였습니다.", ephemeral=True)
        else:
            all_opportunity.remove(user_list[0][1])
            choice = False
            for winners in respond_user:
                score_up(winners)
            for number in range(1, len(user_list)):
                analact_append(number)
            next_round()
            await ctx.respond("모든 유저가 개새끼로 선정 됬습니다!\n다음 술래는 " + user_list[0][1] + "입니다.")


@client.command(guild_ids=[907936221446148138])
async def sample(ctx):
    text = ""
    for x in range(1, 11):
        text = text + random.choice(sample_list)
    await ctx.respond(text, ephemeral=True)


@client.command(guild_ids=[907936221446148138])
async def check(ctx):
    if ctx.author.id is user_list[0][1]:
        await ctx.respond("당신은 술래라 대답할 필요가 없습니다.", ephemeral=True)
    else:
        if ctx.author.id in respond_user:
            await ctx.respond("당신은 이미 대답하였습니다.", ephemeral=True)
        else:
            await ctx.respond("당신은 아직 대답하지 않았습니다. 얼른 대답해 미친놈아", ephemeral=True)


@client.command(guild_ids=[907936221446148138])
async def democracy(ctx):
    global vote_user
    global scaffolded
    if ctx.author.id not in respond_user and ctx.author.id is not user_list[0][1]:
        await ctx.respond("당신은 아직 대답하지 않았으니 모가지 잘리기 전에 어서 대답하세요.", ephemeral=True)
    else:
        if scaffolded is True:
            await ctx.respond("한명을 두번이나 담구는건 좀 너무한거 아닌지?", ephemeral=True)
        else:
            if len(respond_user) == len(user_list) - 2:
                if ctx.author.id in vote_user:  # vote_user는 submit에서 초기화
                    await ctx.respond("이미 투표하였습니다.", ephemeral=True)
                else:
                    vote_user.append(ctx.author.id)
                    if len(vote_user) == 1:
                        await ctx.respond(ctx.author.name + "님이 민주주의 재판을 시작하였습니다! /democracy를 입력하여 본때를 보여주세요!")
                    else:
                        if len(vote_user) > len(user_list) / 2:
                            scaffold = []
                            for user in user_list:
                                scaffold.append(user[0])
                            for respond in respond_user:
                                scaffold.remove(respond)
                            scaffold.remove(user_list[0][1])
                            score_up(scaffold)
                            scaffolded = True
                            await ctx.send(str(len(vote_user)) + "명이 동참하여 아직 답을 제출하지 않은 한명의 스코어가 1올랐습니다! 민주주의 만세!")
                            await ctx.respond("투표가 반영되었습니다.", ephemeral=True)
                        else:
                            await ctx.send(str(len(vote_user)) + "명이 동참하였습니다!")
                            await ctx.respond("투표가 반영되었습니다.", ephemeral=True)
            else:
                await ctx.respond("아직 칼을 뽑을 타이밍이 아닌 것 같습니다.", ephemeral=True)


@client.command(guild_ids=[907936221446148138])
async def help(ctx):
    await ctx.respond("말로하기 귀찮으니까 *미리 작성된 사용법* 으로 대체함\n"
                      "/join 눌러서 게임 등록하고 모두 등록하면 /start + 우승점수 입력하면 시작됨, 답변자 공개는 choice 후 누군지 공개되는 설정임\n"
                      "술래인 사람은 /draw로 카드 뽑고, 카드가 뽑히면 나머지 사람은 /submit으로 정답 제출하면 됨\n"
                      "아직 명령어 못 찾아서 항목 비우기가 안되니까 만약 빈칸이 1개라면 2번, 3번 제출 항목은 그냥 아무거나 적고 넘기면 됨\n"
                      "혹시 자기가 대답했는지 햇갈리면 /check로 확인할 수 있음\n"
                      "모두 제출되면 자동으로 선택지가 표시될거고 술래가 /choice로 몇번 유저를 고를지 고르고 계속 반복하면 됨\n"
                      "코멧이 그토록 염원하던 /choice_all이 게임당 단 1번 제한으로 추가 되었으니 즐겁게 사용하면 됨\n"
                      "만약 단 한명만이 답을 제출하지 않았다면 /democracy를 입력해서 과반수의 동의를 받고 그 사람의 스코어를 1올릴 수 있음\n"
                      "/score로 스코어 중간집계 볼 수 있음(끝나고 나서도 볼 수 있음)\n"
                      "그리고 창의력의 보충을 위해 언제던지 /sample 치면 카드 10장 볼 수 있음\n"
                      "왠만한 에러는 다 잡아두긴 했는데 그래도 빵꾸 있을 수 있으니 찾으면 칭?찬(혹은 도?끼)은 해줌\n"
                      "이번엔 과연 누가 천하의 멍멍이가 될지 기대가 됩니다")

client.run("MTA2OTY2NTE1NTc0NDU0Njg1Ng.GNYCmz.CMME8MchoMHBWvlBXy1bM7ZTQoY4jMDdEUuyAU")
