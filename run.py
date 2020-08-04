import lambda_function

command = ''
channel_id = ''
team_id = ''
user_id = ''
response_url = 'no use'

event = {'body': f"text={command}&channel_id={channel_id}&team_id={team_id}&user_id={user_id}&response_url={response_url}"}

lambda_function.bootstrap(event, {})
