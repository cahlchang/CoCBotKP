import lambda_function


channel_id = 'CNCRFR7KP'
team_id = 'TE4VDPM2L'
user_id = 'UE6P69HFH'
response_url = "no"
channel_name = "local"

command_list = ['init <https://charasheet.vampire-blood.net/2796211>',
                '1D100',
                'result',
                's',
                'status',
                'u',
                'update',
                'u HP+5',
                'update SAN+10',
                'sanc',
                'sanc 1d4/1d20',
                '跳躍',
                'kp start',
                'join UE6P69HFH',
                'キック-20',
                '組み付き*2',
                'こぶし+20',
                'APP*5',
                'dex*2',
                'con',
                '信用/2',
                'list chara 図書館>80',
                'listchara ラテン語',
                'saveimg',
                'loadimg',
                'result',
                'init <https://charasheet.vampire-blood.net/2601601>',
                'join UE6P69HFH',
                'hide 心理学',
                'hide 心理学+20',
                'hide 心理学-20',
                'hide 心理学*2',
                'hide 心理学/2',
                'hide やっほー',
                'result',
                'kp order DEX',
                'kp select',
                'leave UE6P69HFH',
                'kp order DEX',
                'help',
                'openhelp',
                'history <https://charasheet.vampire-blood.net/3395789>',
                'init <https://charasheet.vampire-blood.net/3668130>', # 7版のテスト
                '威圧',
                'ヒプノーシス',
                '威圧 H',
                '威圧 E'
]

for command in command_list:
    event = {'body': f"text={command}&channel_id={channel_id}&team_id={team_id}&user_id={user_id}&response_url={response_url}&channel_name={channel_name}"}
    lambda_function.bootstrap(event, {})
