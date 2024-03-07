import discord
import asyncio
import random
import time

client = discord.Bot(intents=discord.Intents.all())

is_started = False      # 게임 시작 여부
open_respond = False    # 정답 공개 여부
scaffolded = False      # 재판 시행 여부

win_score = 0       # 우승 스코어
respond_slot = 0    # 응답할 항목 갯수

current_card = ""   # 현재 선택된 카드
turn = ""           # 현재 턴 정보

play_order = []         # 진행 순서
drew_card = []          # 뽑은 순서
answer_list = []        # 응답 목록
responded_list = []     # 응답한 유저 목록
voted_list = []         # 재판 투표자 목록

user_dict = {}      # 등록된 유저 목록
analects_dict = {}  # 어록 목록


with open("card.txt", "r", encoding='UTF-8') as cards:
    card_list = []
    for i in cards:
        i = i.replace("_", "_____")
        card_list.append(i)

with open("respond.txt", "r", encoding='UTF-8') as samples:
    sample_list = []
    for i in samples:
        sample_list.append(i)

now = str(time.strftime('%Y.%m.%d %H:%M:%S - '))
print(now + "Data load complete")


def clear_db():
    global is_started
    global user_dict
    global responded_list
    global answer_list
    global voted_list
    global scaffolded

    is_started = False  # 시작 여부 초기화
    user_dict = {}      # 유저 정보 초기화
    responded_list = []     # 답변자 초기화
    answer_list = []        # 답변 초기화
    voted_list = []     # 재판 투표자 초기화
    scaffolded = False  # 재판 시행 여부 초기화

    now = str(time.strftime('%Y.%m.%d %H:%M:%S - '))
    print(now + "Game completed successfully")


def next_round():
    global play_order
    global responded_list
    global answer_list
    global voted_list
    global scaffolded

    first = play_order[0]   # 리스트 회전
    play_order = play_order[1:]
    play_order.append(first)

    responded_list = []     # 답변자 초기화
    answer_list = []        # 답변 초기화
    voted_list = []     # 재판 투표자 초기화
    scaffolded = False  # 재판 시행 여부 초기화


def score_up(user_id):
    global user_dict
    user_dict[user_id]["Score"] = user_dict[user_id]["Score"] + 1


def analects_append(user_id, answer):
    full_answer = current_card
    for i in answer:
        full_answer = full_answer.replace("_____", f"**__{i}__**", 1)
    analects_list = analects_dict[user_id]  # 이전 어록 추출
    analects_list.append(full_answer)       # 어록 추가
    analects_dict[user_id] = analects_list  # 어록 갱신


def win_process(user_id_int_list, ctx):
    def check(user_id):
        if user_dict[user_id]["Score"] >= win_score:
            return True
        else:
            return False

    async def execution(user_id, ctx):
        analects_list = analects_dict[user_id]  # 어록 호출
        text = ">>> "
        for analects in analects_list:
            text = text + analects + "\n"
        message_id = await ctx.send("우승자 " + user_dict[user_id]["Name"] + "의 어록 모음집\n" + text)
        await message_id.pin()

        text = f"**<최종 결과>**\n>>> "
        score_list = []
        for i in user_dict.keys():  # [이름, 스코어] 리스트 생성
            score_list.append([user_dict[i]["Name"], user_dict[i]["Score"]])
        score_list.sort(key=lambda x: -x[1])  # 내부 리스트 1번 인덱스를 기준으로 역순 정렬
        for i, j in score_list:
            text = text + i + ":" + str(j) + "점\n"
        await ctx.send(text)

    async def send_message(text, ctx):
        await ctx.send(text)

    if type(user_id_int_list) == int:   # 일반 처리 과정
        if check(user_id_int_list):     # 우승 확인
            asyncio.create_task(execution(user_id_int_list, ctx))    # 우승시 처리 시행
            return True

    else:   # 초이스 올 처리 과정
        win_user_list = []
        for i in user_id_int_list:  # 우승 확인
            if check(i):
                win_user_list.append(user_id_int_list)  # 우승자 목록 추가

        if len(win_user_list) == 0:     # 우승자 없음
            return False

        elif len(win_user_list) == 1:   # 우승자 발생
            asyncio.create_task(execution(user_id_int_list, ctx))    # 우승시 처리 시행
            return True

        else:                           # 다수 우승자 발생
            asyncio.create_task(send_message("다수의 우승자 동시에 발생하여 추가 라운드가 이어집니다!", ctx))
            return False


@client.command(guild_ids=[907936221446148138, 1215283873278070804])
async def join(ctx):
    global user_dict
    user_id = ctx.author.id
    user_name = ctx.author.name

    if is_started:  # 시작시 등록 불가
        await ctx.respond("게임이 이미 시작되었습니다.")

    elif user_dict.get(user_id) is not None:    # 중복 등록 확인
        await ctx.respond("이미 등록한 유저입니다.", ephemeral=True)

    else:   # 등록
        user_dict[user_id] = {
            "Name": user_name,
            "Score": 0,
            "All": True
        }
        await ctx.respond("성공적으로 등록되었습니다.")


@client.command(guild_ids=[907936221446148138, 1215283873278070804])
async def leave(ctx):
    global user_dict

    if ctx.author.id not in user_dict.keys():   # 게임 참여자가 아닌 경우
        await ctx.respond("게임에 참여하고 있지 않습니다.", ephemeral=True)

    else:
        user_dict.pop(ctx.author.id)
        await ctx.respond("성공적으로 등록이 취소되었습니다.")


@client.command(guild_ids=[907936221446148138, 1215283873278070804])
async def user_list(ctx):
    count = len(user_dict.keys())
    text = f"현재 참여자 목록(총 {count}명)\n>>> "
    for i in user_dict.keys():
        text = text + user_dict[i]["Name"] + "\n"
    await ctx.respond(text, ephemeral=True)


@client.command(guild_ids=[907936221446148138, 1215283873278070804])
async def start(
        ctx,
        score: discord.Option(int),
        open_user: discord.Option(str, choices=["답변자 공개", "답변자 미공개"],),
        update_reward_for_universe: discord.Option(str, choices=["준다", "안준다"])
):
    global is_started
    global turn
    global win_score
    global play_order
    global user_dict
    global analects_dict
    global open_respond
    text = ""

    if ctx.author.id not in user_dict.keys():   # 게임 참여자가 아닌 경우
        await ctx.respond("먼저 게임에 참여해주세요.", ephemeral=True)

    elif is_started:    # 게임이 이미 시작한 경우
        await ctx.respond("게임이 이미 진행중입니다. 먼저 /end로 게임을 끝내주세요.", ephemeral=True)

    elif len(user_dict.keys()) <= 2:    # 참여자가 너무 적은 경우
        await ctx.respond("참여자가 3명 이상이어야만 시작할 수 있습니다.", ephemeral=True)

    elif score <= 0:    # 스코어가 제대로 되지 않은 경우
        await ctx.respond("우승점수는 양의 정수여야 합니다.")

    else:
        is_started = True  # 시작 여부 수정
        turn = "draw"   # 시작 턴 설정
        win_score = score   # 우승 점수 설정
        play_order = list(user_dict.keys())     # 술레 순서 등록
        random.shuffle(play_order)  # 순서 셔플
        for i in play_order:    # 어록 생성
            analects_dict[i] = []

        if open_user == "답변자 공개":
            open_respond = True
        else:
            open_respond = False

        if 278170182227066880 in user_dict.keys() and update_reward_for_universe == "준다":
            user_dict[278170182227066880]["Score"] = 3
            text = "\n유니를 위한 업데이트 사료 3.24점이 제공되었습니다!(청약철회는 받지 않습니다.)"

        now = str(time.strftime('%Y.%m.%d %H:%M:%S - '))
        print(now + "Game started successfully, user = " + ctx.author.name)

        await ctx.respond(
            f"우승점수 {win_score}점으로 게임이 시작되었습니다.\n첫 술래는 {user_dict[play_order[0]]['Name']}입니다.{text}"
        )


@client.command(guild_ids=[907936221446148138, 1215283873278070804])
async def end(ctx):
    if not is_started:  # 게임이 아직 시작하지 않은 경우
        await ctx.respond("아직 게임이 시작하지 않았습니다.", ephemeral=True)

    clear_db()  # 게임 종료 전처리
    now = str(time.strftime('%Y.%m.%d %H:%M:%S - '))
    print(now + "Game canceled midway, user = " + ctx.author.name)
    await ctx.respond("게임이 종료되었습니다.")


@client.command(guild_ids=[907936221446148138, 1215283873278070804])
async def score(ctx):
    if not is_started:  # 게임이 아직 시작하지 않은 경우
        await ctx.respond("아직 게임이 시작하지 않았습니다.", ephemeral=True)

    text = f"우승 점수 : {win_score}\n>>> "
    score_list = []
    for i in user_dict.keys():  # [이름, 스코어] 리스트 생성
        score_list.append([user_dict[i]["Name"], user_dict[i]["Score"]])
    score_list.sort(key=lambda x: -x[1])     # 내부 리스트 1번 인덱스를 기준으로 역순 정렬

    for i, j in score_list:
        text = text + i + ":" + str(j) + "점\n"

    await ctx.respond(text)


@client.command(guild_ids=[907936221446148138, 1215283873278070804])
async def draw(ctx):
    global turn
    global drew_card
    drew_card = []
    text = "```"

    if not is_started:  # 게임이 아직 시작하지 않은 경우
        await ctx.respond("아직 게임이 시작하지 않았습니다.", ephemeral=True)

    elif ctx.author.id != play_order[0]:    # 술래가 아닐 경우
        await ctx.respond("당신의 차례가 아닙니다.", ephemeral=True)

    elif not turn == "draw":  # 드로우 턴이 아닐 경우
        await ctx.respond(f"{turn}을(를) 먼저 해주세요.", ephemeral=True)

    else:
        turn = "select"     # 다음 턴 설정
        while len(drew_card) != 3:  # 카드 5장 드로우
            card = random.choice(card_list)     # 카드 드로우
            if card not in drew_card:   # 중복 확인
                drew_card.append(card)

        count = 1
        for i in drew_card:
            text = text + str(count) + ". " + i + "\n"
            count = count + 1

        text = text + "원하는 카드의 번호를 /select로 입력하세요.```"
	await ctx.send("술레가 카드를 고르는 중입니다.")
        await ctx.respond(text, ephemeral=True)


@client.command(guild_ids=[907936221446148138, 1215283873278070804])
async def select(ctx, number: discord.Option(int)):
    global turn
    global current_card
    global respond_slot

    if not is_started:  # 게임이 아직 시작하지 않은 경우
        await ctx.respond("아직 게임이 시작하지 않았습니다.", ephemeral=True)

    elif ctx.author.id != play_order[0]:    # 술레가 아닐 경우
        await ctx.respond("당신의 차례가 아닙니다.", ephemeral=True)

    elif not turn == "select":  # 셀렉트 턴이 아닐 경우
        await ctx.respond(f"{turn}을(를) 먼저 해주세요.", ephemeral=True)

    elif number > len(drew_card) or number < 1:    # 입력이 잘못 됐을 경우
        await ctx.respond("잘못된 입력입니다.", ephemeral=True)

    else:
        turn = "submit"     # 다음 턴 설정
        current_card = drew_card[number-1]
        respond_slot = current_card.count("_____")
        await ctx.respond("`" + current_card + "`")     # 선택된 카드 공지


@client.command(guild_ids=[907936221446148138, 1215283873278070804])
async def sample(ctx):
    text = ""
    for x in range(10):
        text = text + random.choice(sample_list)
    await ctx.respond(text, ephemeral=True)


@client.command(guild_ids=[907936221446148138, 1215283873278070804])
async def submit(ctx, first, second='', third=''):
    global turn
    global answer_list
    global responded_list

    if not is_started:  # 게임이 아직 시작하지 않은 경우
        await ctx.respond("아직 게임이 시작하지 않았습니다.", ephemeral=True)

    elif turn != "submit" or ctx.author.id == play_order[0]:    # 서브밋 턴이 아니거나 술래일 경우
        await ctx.respond("당신의 차례가 아닙니다.", ephemeral=True)

    elif ctx.author.id in responded_list:   # 응답자 목록에 들어가 있을 경우
        await ctx.respond("이미 응답하였습니다.", ephemeral=True)

    else:
        reply = [ctx.author.id, [first, second, third]]
        reply[1] = reply[1][:respond_slot]    # 필요한 갯수만 슬라이스
        answer_list.append(reply)
        responded_list.append(ctx.author.id)
        await ctx.send(
            str(len(responded_list)) + "명이 응답하였습니다. (" + str(len(play_order)-len(responded_list)-1) + "명 남음)"
        )

        if len(answer_list) == len(play_order) - 1:  # 응답 완료 시 작동
            turn = "choice"    # 다음 턴 설정
            answer_text = f"문장 : {current_card}\n{user_dict[play_order[0]]['Name']}가 고릅니다.\n"
            count = 1
            random.shuffle(answer_list)     # 순서 셔플
            for i in answer_list:   # 응답 병합 및 출력
                text = ", ".join(map(str, i[1]))
                answer_text = answer_text + f"{count}번 유저 : " + text + "\n"
                count = count + 1
            await ctx.send("```" + answer_text + "```")

        await ctx.respond("응답이 기록되었습니다.", ephemeral=True)


@client.command(guild_ids=[907936221446148138, 1215283873278070804])
async def check(ctx):
    if not is_started:
        await ctx.respond("아직 게임이 시작하지 않았습니다.", ephemeral=True)

    elif ctx.author.id is play_order[0]:
        await ctx.respond("당신은 술래라 대답할 필요가 없습니다.", ephemeral=True)

    elif ctx.author.id in responded_list:
        await ctx.respond("당신은 이미 대답하였습니다.", ephemeral=True)

    else:
        await ctx.respond("당신은 아직 대답하지 않았습니다. /submit으로 대답을 입력하세요.", ephemeral=True)


@client.command(guild_ids=[907936221446148138, 1215283873278070804])
async def choice(ctx, number: discord.Option(int)):
    global turn

    if not is_started:  # 게임이 아직 시작하지 않은 경우
        await ctx.respond("아직 게임이 시작하지 않았습니다.", ephemeral=True)

    elif ctx.author.id != play_order[0]:    # 술레가 아닐 경우
        await ctx.respond("당신의 차례가 아닙니다.", ephemeral=True)

    elif turn == "submit":  # 응답이 완료되지 않았을 경우
        await ctx.respond("응답을 기다려주세요.", ephemeral=True)

    elif turn != "choice":  # 초이스 턴이 아닐 경우
        await ctx.respond(f"{turn}을(를) 먼저 해주세요.", ephemeral=True)

    elif number > len(responded_list) or number < 1:    # 입력이 잘못 됐을 경우
        await ctx.respond("잘못된 입력입니다.", ephemeral=True)

    else:
        turn = "draw"   # 다음 턴 설정
        number = number - 1     # 인덱스 보정
        win_user = answer_list[number][0]   # 우승한 유저 선정
        analects_append(win_user, answer_list[number][1])   # 어록 사전 추가
        score_up(win_user)

        if open_respond:    # 발화자 공개
            text = ""
            user_number = 1
            for i in answer_list:
                user_id = i[0]  # 유저 id 추출
                text = text + str(user_number) + "번 유저는 " + user_dict[user_id]['Name'] + "\n"
                user_number += 1
            text = "```" + text + "였습니다!```"
            await ctx.send(text)

        if win_process(win_user, ctx):  # 우승자 체크 및 실행
            await ctx.respond(
                str(number + 1) + "번 유저 " + user_dict[win_user]['Name'] +
                "가 최종 우승입니다! 우리의 새로운 멍멍이를 위해 축하해주세요!"
            )
            clear_db()  # 게임 종료 전처리

        else:   # 우승자가 없을 경우
            next_round()    # 다음 라운드 전처리
            await ctx.respond(
                str(number + 1) + "번 유저 " + user_dict[win_user]['Name'] + "가 우승하였습니다!\n" +
                "다음 술래는 " + user_dict[play_order[0]]['Name'] + "입니다."
            )


@client.command(guild_ids=[907936221446148138, 1215283873278070804])
async def choice_all(ctx):
    global turn

    if not is_started:  # 게임이 아직 시작하지 않은 경우
        await ctx.respond("아직 게임이 시작하지 않았습니다.", ephemeral=True)

    elif ctx.author.id != play_order[0]:  # 술레가 아닐 경우
        await ctx.respond("당신의 차례가 아닙니다.", ephemeral=True)

    elif turn != "choice":  # 초이스 턴이 아닐 경우
        await ctx.respond(f"{turn}을(를) 먼저 해주세요.", ephemeral=True)

    elif user_dict[play_order[0]]["All"] is False:     # 기회가 없을 경우
        await ctx.respond("이미 기회를 소진하였습니다.", ephemeral=True)

    else:
        user_dict[play_order[0]]["All"] = False    # 기회 제거
        turn = "draw"   # 다음 턴 설정

        for i in responded_list:    # 전체 스코어 상승
            score_up(i)

        if win_process(responded_list, ctx):  # 우승자 체크 및 실행
            win_user = None
            for i in responded_list:    # 우승자 추출
                if user_dict[i]["Score"] >= win_score:
                    win_user = i
                    break

            await ctx.respond(
                "모든 유저가 개새끼로 선정 됐습니다!\n" + user_dict[win_user]['Name'] +
                "가 최종 우승입니다! 우리의 새로운 멍멍이를 위해 축하해주세요!"
            )
            clear_db()  # 게임 종료 전처리

        else:
            next_round()    # 다음 라운드 전처리
            await ctx.respond("모든 유저가 개새끼로 선정 됐습니다!\n다음 술래는 " + user_dict[play_order[0]]['Name'] + "입니다.")


@client.command(guild_ids=[907936221446148138, 1215283873278070804])
async def democracy(ctx):
    global voted_list
    global scaffolded

    if not is_started:  # 게임이 아직 시작하지 않은 경우
        await ctx.respond("아직 게임이 시작하지 않았습니다.", ephemeral=True)

    elif ctx.author.id != play_order[0] and ctx.author.id not in responded_list:    # 술래가 아니지만 대답하지 않았을 경우
        await ctx.respond("당신은 아직 대답하지 않았으니 모가지 잘리기 전에 어서 대답하세요.", ephemeral=True)

    elif len(responded_list) != len(play_order) - 2:  # 아직 두명 이상이 대답하지 않았을 경우
        await ctx.respond("아직 칼을 뽑을 타이밍이 아닌 것 같습니다.", ephemeral=True)

    elif len(play_order) <= 4:  # 인원이 너무 적은 경우
        await ctx.respond("인원이 너무 적어 재판을 시행할 수 없습니다.", ephemeral=True)

    elif scaffolded:    # 이번 라운드에 이미 재판이 시행됐을 경우
        await ctx.respond("한명을 두번이나 담구는건 좀 너무한거 아닌지?", ephemeral=True)

    elif ctx.author.id in voted_list:   # 이미 투표했을 경우
        await ctx.respond("이미 투표하였습니다.", ephemeral=True)

    else:
        voted_list.append(ctx.author.id)
        if len(voted_list) == 1:    # 첫 투표일 경우
            await ctx.respond(ctx.author.name + "님이 민주주의 재판을 시작하였습니다! /democracy를 입력하여 본때를 보여주세요!")

        elif len(voted_list) < len(play_order) / 2:     # 찬성 인원이 과반수 이하일 때
            await ctx.send(str(len(voted_list)) + "명이 동참하였습니다!")
            await ctx.respond("투표가 반영되었습니다.", ephemeral=True)

        else:   # 참수 시행
            scaffolded = True   # 재판 시행 여부 수정
            target = play_order[1:]     # 술래 제외 등록
            for i in responded_list:    # 응답자 제외
                target.remove(i)
            if len(target) != 1:    # 오류 감시
                raise IndexError('재판 대상이 두명 이상입니다.')
            score_up(target[0])
            await ctx.send(str(len(voted_list)) + "명이 동참하여 아직 답을 제출하지 않은 한명의 스코어가 1올랐습니다! 민주주의 만세!")
            await ctx.respond("투표가 반영되었습니다.", ephemeral=True)


@client.command(guild_ids=[907936221446148138, 1215283873278070804])
async def help(ctx):
    await ctx.respond(
        "***☆★경★☆ 멍멍이 게임 1.0 정식출시 ☆★축★☆\n\n"
        ">>> 말로하기 귀찮으니까 *미리 작성된 사용법* 으로 대체함\n"
        "`/join` 눌러서 게임 등록하고 모두 등록하면 `/start + 우승점수` 입력하면 시작됨, 답변자 공개시 `/choice` 후 답변자가 누군지 공개됨\n"
        "술래인 사람은 `/draw`로 카드를 3장 뽑고, 그 중 마음에 드는 카드를 `/submit`으로 입력하면 됨\n"
        "카드가 뽑히면 나머지 사람은 `/submit`으로 정답을 제출하면 됨, 좋은 소식은 bing이 명령어 찾아줘서 이젠 second랑 third 비워놔도 됨\n"
        "혹시 자기가 대답했는지 햇갈리면 `/check`로 확인할 수 있음\n"
        "모두 제출되면 자동으로 선택지가 표시될거고 술래가 `/choice`로 몇번 유저를 고를지 고르고 계속 반복하면 됨\n"
        "코멧이 그토록 염원하던 `/choice_all`이 게임당 단 1번 제한으로 추가 되었으니 즐겁게 사용하면 됨\n"
        "만약 단 한명만이 답을 제출하지 않았다면 `/democracy`를 입력해서 과반수의 동의를 받고 그 사람의 스코어를 1올릴 수 있음\n"
        "`/score`로 스코어 중간집계 볼 수 있음\n"
        "그리고 창의력의 보충을 위해 언제던지 `/sample` 치면 카드 10장 볼 수 있음\n"
        "왠만한 에러는 다 잡아두긴 했는데 그래도 빵꾸 있을 수 있으니 찾으면 칭?찬(혹은 도?끼)은 해줌\n"
        "이번엔 과연 누가 천하의 멍멍이가 될지 기대가 됩니다")

with open('token.txt', 'r') as f:
    token = f.read()
