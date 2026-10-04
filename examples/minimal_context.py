"""离线教程示例：冻结虚构对话和记忆，按一种正文表示返回材料。"""
import hashlib
import json
import sys


def recent_rounds(messages, limit=10):
    rounds, current = [], []
    has_user = answered = False
    for message in messages:
        if current and (message['session_id'] != current[0]['session_id'] or
                        (message['role'] == 'user' and answered)):
            rounds.append(current)
            current, has_user, answered = [], False, False
        current.append(message)
        if message['role'] == 'user':
            has_user = True
        elif has_user:
            answered = True
    if current:
        rounds.append(current)
    return rounds[-limit:]


def freeze(messages, trigger_id, recall):
    # 调用者应先完成权限、消息范围、来源与附件校验。
    rounds = recent_rounds(messages)
    selected = [message for group in rounds for message in group]
    triggers = [message for message in selected if message['id'] == trigger_id]
    if len(triggers) != 1:
        raise ValueError('触发消息必须恰好出现一次')
    recalled = recall(triggers[0]['content'], include_recent_context=False)
    snapshot = {'revision': 1, 'round_limit': 10, 'round_count': len(rounds),
                'messages': selected, 'recall': recalled}
    return json.dumps(snapshot, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False)


def read_page(material, offset=0, page_size=24000):
    # offset 是离线演示参数；实际接口应使用绑定请求和摘要的不透明游标。
    if offset < 0 or offset >= len(material) or offset % page_size:
        raise ValueError('无效分页位置')
    small = len(material.encode('utf-8')) <= 64000
    if small and offset:
        raise ValueError('小材料不分页')
    end = len(material) if small else min(len(material), offset + page_size)
    return {'snapshot': None, 'snapshot_json': material if small else None,
            'snapshot_json_part': None if small else material[offset:end],
            'snapshot_sha256': hashlib.sha256(material.encode('utf-8')).hexdigest(),
            'material_bytes': len(material.encode('utf-8')),
            'next_offset': end if end < len(material) else None,
            'complete': end == len(material)}


def demo(large=False):
    extra = '虚构长文本 😀 ' * 10000 if large else ''
    messages = [
        {'id': 1, 'session_id': 1, 'role': 'user', 'source': 'chat', 'content': '虚构对话：想做一个书架。'},
        {'id': 2, 'session_id': 1, 'role': 'assistant', 'source': 'local_model', 'content': '虚构对话：先量一下墙面。'},
        {'id': 3, 'session_id': 1, 'role': 'user', 'source': 'chat', 'content': '@ChatGPT（官端） 请继续书架设计。' + extra},
    ]
    calls = []
    def recall(query, include_recent_context):
        calls.append(query)
        assert include_recent_context is False
        return {'status': 'ok', 'notes': [{'id': 'synthetic_memory', 'text': '虚构记忆：需要一格放绘本。'}]}
    material = freeze(messages, 3, recall)
    pages, offset = [], 0
    while True:
        page = read_page(material, offset)
        pages.append(page)
        if page['complete']:
            break
        offset = page['next_offset']
    restored = pages[0]['snapshot_json'] or ''.join(page['snapshot_json_part'] for page in pages)
    assert restored == material and len(calls) == 1
    print(json.dumps({'offline': True, 'model_calls': 0, 'recall_calls': len(calls),
                      'round_count': json.loads(material)['round_count'], 'pages': len(pages),
                      'digest_matches': hashlib.sha256(restored.encode()).hexdigest() == pages[0]['snapshot_sha256']},
                     ensure_ascii=False))
    return pages


if __name__ == '__main__':
    demo(large='--large' in sys.argv)
