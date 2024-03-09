import os

with open("sibal_Mk.2.py", "r", encoding='UTF-8') as original:
    original_contents = original.readlines()    # 기존 내용 백업

sever_id = input("서버의 ID를 입력해주세요.\n> ").strip()

adding = f"@client.command(guild_ids=[{sever_id}])\n"
new_contents = []

for i in original_contents:
    if "@client.command" in i:  # 서버 ID 부분 대체
        new_contents.append(adding)
    else:                       # 아닌 부분은 그대로
        new_contents.append(i)

with open("sibal_Mk.2.py", "w", encoding='UTF-8') as new:
    new.writelines(new_contents)    # 수정된 내용 덮어씌우기

print("처리가 완료되었습니다.")
os.system("pause")
