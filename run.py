import lambda_function

#test
command = ''
channel_id = 'CNCRFR7KP'
team_id = 'TE4VDPM2L'
user_id = 'UE6P69HFH'
response_url = 'no use'
channel_name = 'local'

event = {'body': f"text={command}&channel_id={channel_id}&team_id={team_id}&user_id={user_id}&response_url={response_url}&channel_name={channel_name}"}

lambda_function.bootstrap(event, {})
