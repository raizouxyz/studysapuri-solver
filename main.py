import time
import uuid
import random
import requests

token = "" # Authorizationヘッダ(前方のToken なし)
session_key = "" # question_answeredかtopic_attemptedのparams->session_key
correct_percentage = 80 # 正答率をパーセントで入力
skip_lesson = False

headers = {
    "Authorization": f"Token {token}",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
}

def seconds_to_string(_seconds):
    minutes = str(int(_seconds / 60)).zfill(2)
    seconds = str(_seconds % 60).zfill(2)
    return f"{minutes}:{seconds}"

response = requests.get("https://learn.studysapuri.jp/qlearn/v1/bootstrap", headers=headers)
if response.status_code == 200:
    bootstrap = response.json()
    response = requests.get("https://learn.studysapuri.jp/qlearn/v1/todo?active=true&completed=false&page=0&per_page=20", headers=headers)
    print("GetTodo", response.status_code, response.text)
    todos = response.json()
    for todo in todos:
        response = requests.get(f"https://learn.studysapuri.jp/qlearn/v1/schedule/{todo['id']}/topics/{','.join(todo['todo_topic_ids'])}/usage", headers=headers)
        topics = response.json()
        print("GetTopics", response.status_code)
        for topic in topics:
            response = requests.get(f"https://learn.studysapuri.jp/qlearn/v1/schedule/{todo['id']}/topic/{topic['id']}/contents", headers=headers)
            contents = response.json()
            print("GetContents", response.status_code)
            response = requests.get(f"https://learn.studysapuri.jp/qlearn/v1/schedule/{todo['id']}/topic/{topic['id']}/usage_with_questions", headers=headers)
            usage_with_questions = response.json()
            print("GetUsageWithQuestions", response.status_code)
            # lesson
            if not skip_lesson:
                for lesson in contents["lessons"]:
                    if usage_with_questions["lessons"][lesson["index_to_chapter_type"]-1]["viewed"] == False:
                        if lesson["chapter_type"] == "video":
                            for chapter in lesson["chapters"]:
                                print(f"宿題名:{todo['name']}, 教材:{contents['course_name']} -> {topic['name']} -> {contents['bundle_name']} -> {chapter['title']}")
                                for section in chapter["sections"]:
                                    duration_seconds = section["section_content"]["duration_seconds"]
                                    request_payload = {"commits":[{"action":"video_attempt","action_ts":int(time.time()),"params":{"chapter_id":chapter["id"],"video_current_position":0,"video_playback_speed":100,"video_prev_position":0,"video_start_position":0,"enable_video_subtitles":False,"can_use_video_subtitles":False},"uuid":str(uuid.uuid4()),"student_id":bootstrap["user"]["id"]}]}
                                    headers["X-Sapuri-Commit-Post-At"] = str(int(time.time()))
                                    response = requests.post("https://learn.studysapuri.jp/v1/commits", headers=headers, json=request_payload)
                                    headers.pop("X-Sapuri-Commit-Post-At")
                                    print("VideoAttemptFirst", response.status_code)
                                    for minutes in range(int(duration_seconds / 60)):
                                        video_current_position = minutes * 60
                                        if minutes == 0:
                                            video_prev_position = 0
                                        else:
                                            video_prev_position = (minutes - 1) * 60
                                        request_payload = {"commits":[{"action":"video_attempt","action_ts":int(time.time()),"params":{"chapter_id":chapter["id"],"video_current_position":video_current_position,"video_playback_speed":100,"video_prev_position":video_prev_position,"video_start_position":0,"enable_video_subtitles":False,"can_use_video_subtitles":False},"uuid":str(uuid.uuid4()),"student_id":bootstrap["user"]["id"]}]}
                                        headers["X-Sapuri-Commit-Post-At"] = str(int(time.time()))
                                        response = requests.post("https://learn.studysapuri.jp/v1/commits", headers=headers, json=request_payload)
                                        headers.pop("X-Sapuri-Commit-Post-At")
                                        print("VideoAttempt", response.status_code)
                                        print(f"VideoAttempt {seconds_to_string(video_current_position)}/{seconds_to_string(duration_seconds)}")
                                        time.sleep(60)
                                    if (duration_seconds % 60) > 0:
                                        time.sleep(duration_seconds % 60)
                                        video_current_position = duration_seconds
                                        video_prev_position = int(duration_seconds / 60) * 60
                                        request_payload = {"commits":[{"action":"video_attempt","action_ts":int(time.time()),"params":{"chapter_id":chapter["id"],"video_current_position":video_current_position,"video_playback_speed":100,"video_prev_position":video_prev_position,"video_start_position":0,"enable_video_subtitles":False,"can_use_video_subtitles":False},"uuid":str(uuid.uuid4()),"student_id":bootstrap["user"]["id"]}]}
                                        headers["X-Sapuri-Commit-Post-At"] = str(int(time.time()))
                                        response = requests.post("https://learn.studysapuri.jp/v1/commits", headers=headers, json=request_payload)
                                        headers.pop("X-Sapuri-Commit-Post-At")
                                        print("VideoAttempt", response.status_code)
                                        print(f"VideoAttempt {seconds_to_string(video_current_position)}/{seconds_to_string(duration_seconds)}")
                        elif lesson["chapter_type"] == "read_aloud_training":
                            for chapter in lesson["chapters"]:
                                request_payload = {"commits":[{"action":"topic_lesson_viewed","action_ts":int(time.time()),"params":{"topic_id":contents["id"],"viewed_chapter_ids":[chapter["id"]]},"uuid":str(uuid.uuid4()),"student_id":bootstrap["user"]["id"]}]}
                                headers["X-Sapuri-Commit-Post-At"] = str(int(time.time()))
                                response = requests.post("https://learn.studysapuri.jp/v1/commits", headers=headers, json=request_payload)
                                headers.pop("X-Sapuri-Commit-Post-At")
            # question
            for question in contents["questions"]:
                time.sleep(random.randint(20, 30))
                correct = random.choices([True, False], weights=[1, 100 / correct_percentage - 1])[0]
                choices = []
                if correct:
                    for choice in question["choices"]:
                        if choice["correct"]:
                            choices.append(choice["id"])
                else:
                    for choice in question["choices"][0:question["correct_answers_count"]]:
                        choices.append(choice["id"])
                request_payload = {"commits":[{"action":"question_answered","params":{"choices":choices,"question_id":question["id"],"session_key":session_key,"correct":correct},"action_ts":int(time.time()),"uuid":str(uuid.uuid4())}]}
                response = requests.post("https://learn.studysapuri.jp/v1/commits", headers=headers, json=request_payload)
                print("AnswerQuestion", response.status_code)
                print("AnswerQuestion", correct)
            request_payload = {"commits":[{"action":"topic_attempted","params":{"session_key":session_key,"topic_id":topic["id"]},"action_ts":int(time.time()),"uuid":str(uuid.uuid4())}]}
            response = requests.post("https://learn.studysapuri.jp/v1/commits", headers=headers, json=request_payload)
            print("TopicAttempt", response.status_code)