import lambda_function

command = 'help'
channel_id = 'CNCRFR7KP'
team_id = 'TE4VDPM2L'
user_id = 'UE6P69HFH'
response_url = 'no use'

event = {'body': f"text={command}&channel_id={channel_id}&team_id={team_id}&user_id={user_id}&response_url={response_url}"}

lambda_function.bootstrap(event, {})
