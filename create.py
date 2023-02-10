import re

to_delete = [
    '''Porządek dzienny.
Sprawy formalne''', 'Sprawy formalne', 
    'Projekt ustawy o Planie Strategicznym dla wspólnej polityki rolnej',
    '''Projekt ustawy o świadczeniu pieniężnym przysługującym członkom rodziny funkcjonariuszy 
lub żołnierzy zawodowych, których śmierć nastąpiła w związku ze służbą 
albo podjęciem poza służbą czynności ratowania życia lub zdrowia ludzkiego albo mienia''', 
'Projekt ustawy o Krajowej Sieci Onkologicznej',
'Punkty 1. i 3. porządku dziennego – głosowanie',
'Projekt ustawy o zmianie ustaw w celu likwidowania zbędnych barier administracyjnych i prawnych',
'Projekt ustawy o finansowaniu wspólnej polityki rolnej na lata 2023–2027',
'Projekt ustawy o zmianie ustawy o cudzoziemcach',
'Projekt ustawy o zmianie ustawy – Kodeks postępowania cywilnego',
'Projekt ustawy o zmianie niektórych ustaw w związku z wprowadzeniem świadczenia za długoletnią służbę',
'''Projekt ustawy o zmianie ustawy o szczególnych rozwiązaniach w zakresie niektórych źródeł ciepła  
w związku z sytuacją na rynku paliw''',
'''Projekt ustawy o zmianie ustawy o szczególnych rozwiązaniach w zakresie niektórych źródeł ciepła  
w związku z sytuacją na rynku paliw. Oświadczenia poselskie''',
'Oświadczenia poselskie',
'71. posiedzenie Sejmu w dniu 25 stycznia 2023 r.'
]

def clean(text, list_to_delete):
    for i in list_to_delete:
        text = text.replace(i, '')
    text = text.replace(' -\n', '')
    text = text.replace('-\n', '')
    text = re.sub(r'(\.|,|\?|\:)(\\S)', r'(\.|,|\?|\:)(\\s)', text)
    text = text.replace('  ', ' ')
    text = text.replace(' )', ')')
    text = text.replace('( ', '(')
    text = text.split("(Na posiedzeniu przewodniczą")

    return text

def beginning(contents):

    content_list = contents.splitlines()

    header = ' '.join(content_list[:3]).strip()
    term = content_list[3]
    title = content_list[4]
    number = content_list[5]
    date = content_list[6]
    day_of_proceedings = content_list[7]
    place = content_list[8]
    year = content_list[9]

    single_number = re.findall(r'(\d*\.)', number)
    title_contents = f'''SPIS TREŚCI
{single_number[0]} posiedzenie Sejmu
(Obrady {date})'''

    return (header, term, title, number, date, day_of_proceedings, place, year, title_contents) 

def table_of_contents(contents):
    contents = contents.split('\n\n\n', 1)
    segments = contents[1].split('\n\n')

    segment_dicts = []
    for segment in segments:
        seg_lines = segment.splitlines()
        seg_dict = {'point': [],
                    'people': []}
        people = []
        point = []
        for e, i in enumerate(seg_lines):
            if ('. . . . .') in i:
                people.append(i)
                seg_dict['people'].append(i)
            elif i.startswith(('Punkt', 'Oświadczenia', 'Załącznik', 'Otwarcie', 'Komunikaty', 'Sprawy')):
                new_point = []
                while '. . . . .' not in seg_lines[e]:
                    new_point.append(seg_lines[e])
                    e=e+1
                point.append(' '.join(new_point).strip())
                seg_dict['point'].append(' '.join(new_point).strip())

        segment_dicts.append(seg_dict)
    
    return segment_dicts

def transcript(text):
    text_list = text.splitlines()
    
    speakers = []
    for i in text_list:
        if i.endswith(':') and not i.endswith(('ustaw:', 'Komisji:')):
            speakers.append(i)
    
    footnotes = []
    for i in text_list:
        if i.startswith('*)'):
            footnotes.append(i)
    
    editorial_note = ' '.join(text_list[-3:]).strip()
    edit = text_list[-3:]
    info, copies = edit[1].split('Nakład')
    ISSN, price = edit[2].split('. ')

    utterances = []
    speakers_ind = []
    for e, i in enumerate(text_list):
        if i in speakers:
            speakers_ind.append(e)
    for e, i in enumerate(speakers_ind):
        try:
            utterance = text_list[i:speakers_ind[e+1]]
            utterances.append(' '.join(utterance))
        except:
            utterance = text_list[i:i+2]
            utterances.append(' '.join(utterance))
    return speakers, footnotes, editorial_note, copies, ISSN, price, utterances

def appendix(text):
    text1 = text.split('Załącznik')
    text2 = text1[1].split('TŁOCZONO')

    s = text2[0].split('\n\n')
    seg_dicts = []
    for segment in s:
        seg_lines = segment.splitlines()
        seg_dict = {'name': [],
                    'party': [],
                    'speech': []}
        for e, i in enumerate(seg_lines):
            if i.startswith('Poseł'):
                seg_dict['name'].append(i)
                seg_dict['party'].append(seg_lines[e+1])
                seg_dict['speech'].append(' '.join(seg_lines[e+2:]))

        seg_dicts.append(seg_dict)
    
    return seg_dicts


def write_xml(xmlfile, table_of_contents, segments, utterances, footnotes, editorial_note, copies, ISSN, price, appendix):
    info = ["header", "term", "title", "number", "date", "day_of_proceedings", "place", "year", "title"]
    with open (xmlfile, "w") as f:
        f.write("<?xml version='1.0' encoding='UTF-8' standalone='no' ?>\n")
        f.write("<body>\n")
        f.write("<header>\n")

        for e, data in enumerate(table_of_contents):
            f.write(f"<{info[e]}>{data}</{info[e]}>\n")
        f.write("</header>\n")
        f.write("<table_of_contents>\n")
        for i in segment_dicts:
            i = list(i.values())
            point = ' '.join(i[0])
            if len(point) > 0:
                f.write(f"<point>{point}</point>\n")
            for person in i[1]:
                element = person.split(' .', 1)
                name = element[0]
                rest = element[1]
                f.write(f"<speech_page><speaker>{name}</speaker>{rest}</speech_page>\n")
        f.write("</table_of_contents>\n")

        f.write("<transcript>\n")
        for i in utterances:                
            segment = i.split(':', 1)
            speaker = segment[0]
            utterance = segment[1]
            side_comments = re.findall(r'(\(.*?\))', utterance)
            tagged = []
            for comment in side_comments:
                if comment in utterance and comment not in tagged:
                    utterance = utterance.replace(comment, f'<side_comment>{comment}</side_comment>\n')
                    tagged.append(comment)
            for footnote in footnotes:
                if footnote in utterance:
                    utterance = utterance.replace(footnote, f'<footnote>{footnote}</footnote>\n')

            f.write(f"<utterance presented='True'><speaker>{speaker}</speaker>{utterance}</utterance>\n")
        f.write("</transcript>\n")
        f.write("<appendix>\n")
        
        for i in appendix:
            i = list(i.values())
            if len(i[0]) > 0:
                f.write('<speech>\n')
                name = ' '.join(i[0])
                party = ' '.join(i[1])
                speech = ' '.join(i[2])
                f.write(f'<speaker>{name}</speaker>\n')
                f.write(f'<party>{party}</party>\n')
                f.write(f'<utterance presented="False">{speech}</utterance></speech>\n')
        
        f.write("</appendix>\n")

        if copies in editorial_note:
            editorial_note = editorial_note.replace(copies, f'<copies>{copies}</copies>\n')
        if ISSN in editorial_note:
            editorial_note = editorial_note.replace(ISSN, f'<ISSN>{ISSN}</ISSN>\n')
        if price in editorial_note:
            editorial_note = editorial_note.replace(price, f'<price>{price}</price>\n')
        
        f.write(f"<edit_note>{editorial_note}</edit_note>\n")

        f.write("</body>\n")

# text = clean(text)
# with open('clean.txt', 'w') as f:
#     f.writelines(text)
with open('clean.txt', 'r') as f:
    text = f.read()

contents, text = clean(text, to_delete)
metadata = beginning(contents)
speakers, footnotes, editorial_note, copies, ISSN, price, utterances = transcript(text)
segment_dicts = table_of_contents(contents)
appendix = appendix(text)

write_xml('transcript.xml', metadata, segment_dicts, utterances, footnotes, editorial_note, copies, ISSN, price, appendix)

