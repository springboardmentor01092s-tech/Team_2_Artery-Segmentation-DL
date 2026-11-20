import collections, hashlib, json, struct, zlib, zipfile
from pathlib import Path, PurePosixPath

root = Path('/tmp/corovision-official-intake')
mapping = Path('../experiments/advanced_preparation_20261026/arcade_source_reconciliation_20261027/annotation_mapping_20261029.json')
def digest(data):
    return hashlib.sha256(data).hexdigest()
def members(name):
    with zipfile.ZipFile(root / (name + '.tail')) as archive:
        return {item.filename: item for item in archive.infolist()}
def decode_member(path, info):
    raw = path.read_bytes()
    signature, _, flags, method, _, _, _, _, _, name_size, extra_size = struct.unpack_from('<4s5H3I2H', raw)
    assert signature == b'PK\x03\x04' and method == info.compress_type == 8 and not flags & 1
    assert raw[30:30+name_size].decode() == info.filename
    start = 30 + name_size + extra_size
    data = zlib.decompress(raw[start:start+info.compress_size], -15)
    assert len(data) == info.file_size and zlib.crc32(data) == info.CRC
    return data
arcade = members('arcade')
cadica = members('cadica')
receipt = dict(scope='ZIP central directories and development COCO JSON only. No image decoding, mask rasterization or inference.',
    arcade_index_range=[450525237,451573812], cadica_index_range=[3067723571,3076112178],
    arcade_index_sha256=digest((root/'arcade.tail').read_bytes()),
    cadica_index_sha256=digest((root/'cadica.tail').read_bytes()),
    saved_mapping_sha256=digest(mapping.read_bytes()),
    arcade_png_counts=dict(collections.Counter('/'.join(n.split('/')[1:3]) for n in arcade if n.endswith('.png'))),
    cadica_member_counts=dict(collections.Counter(PurePosixPath(n).suffix or 'directory' for n in cadica)),
    cadica_selected_video_list_counts={suffix: sum(n.endswith(suffix) for n in cadica)
        for suffix in ('/lesionVideos.txt', '/nonlesionVideos.txt', '_selectedFrames.txt')},
    arcade_validation={})
fingerprints = collections.defaultdict(list)
cadica_readme = decode_member(root / 'cadica-readme.member', cadica['CADICA/readme.txt'])
receipt['cadica_readme_range'] = [1281895244, 1281896700]
receipt['cadica_readme_sha256'] = digest(cadica_readme)
for name, member in arcade.items():
    if name.endswith('.png'):
        fingerprints[(member.file_size, member.CRC)].append(name)
receipt['arcade_crc_size_groups'] = dict(
    repeated=sum(len(names) > 1 for names in fingerprints.values()),
    cross_split=sum(len({n.split('/')[2] for n in names}) > 1 for names in fingerprints.values()),
    limitation='CRC32 plus length is an archive metadata screen. Near duplicates and checkpoint exposure remain unknown.')
for result in json.loads(mapping.read_text())['results']:
    task = result['task']
    if result['split'] != 'val':
        continue
    prefix = f'arcade/{task}/val/'
    data = decode_member(root / (task + '.member'), arcade[prefix+'annotations/val.json'])
    coco = json.loads(data)
    images = {i['id']: i for i in coco['images']}
    annotations = collections.defaultdict(list)
    for annotation in coco['annotations']:
        assert annotation['image_id'] in images
        annotations[annotation['image_id']].append(annotation)
    assert len(images) == len(result['evidence']) == len(coco['images'])
    for row in result['evidence']:
        key = row['coco_image_id']
        assert images[key]['file_name'] == row['coco_filename']
        assert prefix+'images/'+row['coco_filename'] in arcade
        assert sorted(a['id'] for a in annotations[key]) == sorted(row['annotation_ids'])
    receipt['arcade_validation'][task] = dict(coco_sha256=digest(data),
        agrees_with_saved_coco_hash=digest(data)==result['coco_sha256'],
        images=len(images), annotations=len(coco['annotations']), correspondence_matches=len(result['evidence']),
        box_records=sum(len(a.get('bbox',[]))==4 for a in coco['annotations']),
        polygon_records=sum(isinstance(a.get('segmentation'),list) and bool(a['segmentation']) for a in coco['annotations']))
print(json.dumps(receipt, indent=2))
