from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
import json
import os
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.units import inch, cm

app = Flask(__name__)
DATA_FILE = 'spm_data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def count_all_students(data):
    total = 0
    for cls, studs in data.get('students_by_class', {}).items():
        total += len(studs)
    return total

def count_all_subjects(data):
    total = 0
    for cat, subjs in data.get('subject_headcount', {}).items():
        total += len(subjs)
    return total

@app.route('/')
def index():
    data = load_data()
    total_students = count_all_students(data)
    total_subjects = count_all_subjects(data)
    return render_template('index.html', data=data, total_students=total_students, total_subjects=total_subjects)

@app.route('/students')
def students_page():
    data = load_data()
    form_filter = request.args.get('form', '')
    class_filter = request.args.get('class', '')
    return render_template('students.html', data=data, form_filter=form_filter, class_filter=class_filter)

@app.route('/subjects')
def subjects_page():
    data = load_data()
    form_filter = request.args.get('form', '1')
    fn = int(form_filter)
    uat = data.get('uat_data', {})
    form_classes = sorted([c for c in uat.keys() if get_form_number(c) == fn])
    # Gather actual subjects per class
    class_subjects = {}
    for cls in form_classes:
        actual = {}
        for s in uat.get(cls, []):
            for sname, sd in s.get('subjects', {}).items():
                if sd.get('grade', '') or sd.get('mark', ''):
                    actual[sname] = True
        subj_order = uat.get(cls, [{}])[0].get('subject_order', []) if uat.get(cls) else []
        class_subjects[cls] = [sn for sn in subj_order if sn in actual]
    # Gather unique subjects across form
    all_subjs = []
    seen = set()
    for cls in form_classes:
        for sn in class_subjects.get(cls, []):
            if sn not in seen:
                all_subjs.append(sn)
                seen.add(sn)
    return render_template('subjects.html', data=data, form_filter=form_filter,
                           form_classes=form_classes, class_subjects=class_subjects,
                           all_subjects=all_subjs)

@app.route('/subject/<category>/<int:idx>')
def subject_detail(category, idx):
    data = load_data()
    subjects = data.get('subject_headcount', {}).get(category, [])
    subject = subjects[idx] if idx < len(subjects) else None
    return render_template('subject_detail.html', subject=subject, category=category, data=data)

def _get_student_marks_for_exam(data, cls, exam_filter):
    """Get student marks for a given class and exam.
    For UAT: use uat_data directly.
    For other exams: use marks_data (manually entered).
    Returns list of dicts with 'name' and per-subject {'mark', 'grade'}.
    """
    uat = data.get('uat_data', {})
    cls_students = uat.get(cls, [])
    if not cls_students:
        return [], []

    # Get subject list from uat_data (always the reference)
    actual_subjects = {}
    for s in cls_students:
        for sname, sd in s.get('subjects', {}).items():
            if sd.get('grade', '') or sd.get('mark', ''):
                actual_subjects[sname] = True
    subj_order = cls_students[0].get('subject_order', []) if cls_students else []
    subjects_list = [sn for sn in subj_order if sn in actual_subjects]

    if exam_filter == 'UAT':
        # Use uat_data directly
        results = []
        for s in cls_students:
            student_marks = {}
            for subj in subjects_list:
                sd = s.get('subjects', {}).get(subj, {})
                student_marks[subj] = {'mark': sd.get('mark', ''), 'grade': sd.get('grade', '')}
            results.append({'name': s.get('name', ''), 'subjects': student_marks})
        return results, subjects_list
    else:
        # Use marks_data for other exams
        saved_marks = data.get('marks_data', {}).get(cls, {})
        results = []
        for s in cls_students:
            student_name = s.get('name', '')
            student_marks = {}
            sm = saved_marks.get(student_name, {}).get(exam_filter, {})
            for subj in subjects_list:
                m = sm.get(subj, '')
                if m == 'TH':
                    student_marks[subj] = {'mark': 'TH', 'grade': 'TH'}
                elif m != '' and m is not None:
                    try:
                        mark_val = float(m)
                        g, _ = calc_grade(mark_val)
                        student_marks[subj] = {'mark': mark_val, 'grade': g}
                    except (ValueError, TypeError):
                        student_marks[subj] = {'mark': '', 'grade': ''}
                else:
                    student_marks[subj] = {'mark': '', 'grade': ''}
            results.append({'name': student_name, 'subjects': student_marks})
        return results, subjects_list

@app.route('/headcount')
def headcount_page():
    data = load_data()
    form_filter = request.args.get('form', '1')
    exam_filter = request.args.get('exam', 'UAT')
    fn = int(form_filter)
    is_upper = fn >= 4
    grade_cols = ['A+', 'A', 'A-', 'B+', 'B', 'C+', 'C', 'D', 'E', 'G'] if is_upper else ['A', 'B', 'C', 'D', 'E', 'F']

    uat = data.get('uat_data', {})
    form_classes = sorted([c for c in uat.keys() if get_form_number(c) == fn])

    class_headcounts = []
    for cls in form_classes:
        student_marks_list, subjects_list = _get_student_marks_for_exam(data, cls, exam_filter)
        num_students = len(student_marks_list)

        subj_hc = []
        for subj in subjects_list:
            grade_dist = {g: 0 for g in grade_cols}
            th_count = 0
            total_marks = 0
            mark_count = 0
            hadir = 0
            for sm in student_marks_list:
                sd = sm['subjects'].get(subj, {})
                g = sd.get('grade', '')
                m = sd.get('mark', '')
                if g == 'TH' or m == 'TH':
                    th_count += 1
                elif g in grade_dist:
                    grade_dist[g] += 1
                    hadir += 1
                    if isinstance(m, (int, float)):
                        total_marks += m
                        mark_count += 1
                elif g and g not in ('', None):
                    hadir += 1
                    if isinstance(m, (int, float)):
                        total_marks += m
                        mark_count += 1
            total_graded = sum(grade_dist.values())
            lulus_count = sum(grade_dist[g] for g in grade_cols if g not in ('F', 'G'))
            gpmp = 0
            if is_upper:
                gp_map = {'A+': 1, 'A': 2, 'A-': 3, 'B+': 4, 'B': 5, 'C+': 6, 'C': 7, 'D': 8, 'E': 9, 'G': 0}
                total_gp = sum(grade_dist[g] * gp_map.get(g, 0) for g in grade_cols)
                gpmp = (total_gp / total_graded) if total_graded > 0 else 0
            else:
                gp_map = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6}
                total_gp = sum(grade_dist[g] * gp_map.get(g, 0) for g in grade_cols)
                gpmp = (total_gp / total_graded) if total_graded > 0 else 0

            subj_hc.append({
                'subject': subj,
                'daftar': num_students,
                'hadir': hadir,
                'grades': grade_dist,
                'grades_pct': {g: (grade_dist[g] / total_graded * 100) if total_graded > 0 else 0 for g in grade_cols},
                'th': th_count,
                'lulus': lulus_count,
                'lulus_pct': (lulus_count / total_graded * 100) if total_graded > 0 else 0,
                'gagal': total_graded - lulus_count,
                'gagal_pct': ((total_graded - lulus_count) / total_graded * 100) if total_graded > 0 else 0,
                'gpmp': gpmp,
            })
        class_headcounts.append({
            'class': cls,
            'subjects': subj_hc,
            'total_students': num_students,
        })

    current_exams = EXAM_LIST_F5 if fn == 5 else EXAM_LIST
    return render_template('headcount.html', data=data, form_filter=form_filter,
                           exam_filter=exam_filter, grade_cols=grade_cols,
                           class_headcounts=class_headcounts, form_classes=form_classes,
                           exams=current_exams, exam_labels=EXAM_LABELS,
                           exam_label=EXAM_LABELS.get(exam_filter, exam_filter),
                           is_upper=is_upper)

@app.route('/analysis')
def analysis_page():
    data = load_data()
    # Get actual school subjects from uat_data
    uat = data.get('uat_data', {})
    school_subjects = set()
    for cls_students in uat.values():
        for s in cls_students:
            for sname, sd in s.get('subjects', {}).items():
                if sd.get('grade', '') or sd.get('mark', ''):
                    school_subjects.add(sname.strip())

    # Filter analysis_kpi to only school subjects (remove empty SUBTOTAL groups)
    filtered_kpi = []
    if data.get('analysis_kpi'):
        group_buf = []
        has_match = False
        for entry in data['analysis_kpi']:
            subj = (entry.get('subject') or '').strip()
            if entry.get('bil') == 'SUBTOTAL':
                if has_match:
                    group_buf.append(entry)
                    filtered_kpi.extend(group_buf)
                group_buf = []
                has_match = False
            else:
                if subj in school_subjects:
                    group_buf.append(entry)
                    has_match = True
        if has_match:
            filtered_kpi.extend(group_buf)

    # Filter analysis_hc to only school subjects
    filtered_hc = []
    if data.get('analysis_hc'):
        for entry in data['analysis_hc']:
            subj = (entry.get('subject') or '').strip()
            if subj in school_subjects:
                filtered_hc.append(entry)

    # Filter hc_by_exam to only school subjects
    filtered_hc_exam = {}
    if data.get('hc_by_exam'):
        for exam_name, subjects in data['hc_by_exam'].items():
            filtered = [s for s in subjects if (s.get('name') or '').strip() in school_subjects]
            if filtered:
                filtered_hc_exam[exam_name] = filtered

    data['analysis_kpi'] = filtered_kpi
    data['analysis_hc'] = filtered_hc
    data['hc_by_exam'] = filtered_hc_exam
    
    # Add SPM historical data for trend analysis
    spm_hist = data.get('spm_historical', {})
    if spm_hist:
        # Filter SPM subjects to only school subjects
        spm_subjects = {}
        for subject, years_data in spm_hist.get('subjects', {}).items():
            if subject in school_subjects:
                spm_subjects[subject] = years_data
        data['spm_historical']['subjects'] = spm_subjects
    
    return render_template('analysis.html', data=data)

@app.route('/spm-historical')
def spm_historical_page():
    data = load_data()
    return render_template('spm_historical.html', data=data)

@app.route('/individual/<sheet_id>')
def individual_page(sheet_id):
    data = load_data()
    sheet = data.get('individual_sheets', {}).get(sheet_id)
    return render_template('individual.html', sheet=sheet, sheet_id=sheet_id, data=data)

@app.route('/add-student', methods=['GET', 'POST'])
def add_student():
    data = load_data()
    if request.method == 'POST':
        form = request.json
        cls = form.get('class', '')
        if cls not in data.get('students_by_class', {}):
            data.setdefault('students_by_class', {})[cls] = []
        existing = data['students_by_class'][cls]
        new_bil = len(existing) + 1
        student = {
            'bil': new_bil,
            'name': form.get('name', ''),
            'class': cls,
            'form': form.get('form', 'T5')
        }
        existing.append(student)
        save_data(data)
        return jsonify({'success': True})
    return render_template('add_student.html', data=data)

@app.route('/print/summary')
def print_summary():
    data = load_data()
    si = data.get('school_info', {})
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm)
    elements = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('T', parent=styles['Heading1'], fontSize=14, textColor=colors.HexColor('#1e40af'), spaceAfter=20, alignment=1)
    sub_style = ParagraphStyle('S', parent=styles['Heading2'], fontSize=11, alignment=1, spaceAfter=10)

    elements.append(Paragraph(si.get('state', 'JABATAN PENDIDIKAN NEGERI PERLIS'), sub_style))
    elements.append(Paragraph(f"RINGKASAN KESELURUHAN SPM {si.get('exam_year', 2026)}", title_style))
    elements.append(Paragraph(si.get('school_name', ''), sub_style))
    elements.append(Spacer(1, 15))

    info_data = [
        ['Kod Sekolah', str(si.get('school_code', '')), 'Gred Sekolah', str(si.get('school_grade', ''))],
        ['Pengetua', str(si.get('principal', '')), 'Tingkatan', str(si.get('form', ''))],
    ]
    t = Table(info_data, colWidths=[2.5*cm, 6*cm, 2.5*cm, 6*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e5e7eb')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#e5e7eb')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 15))

    elements.append(Paragraph("SENARAI PELAJAR MENGIKUT KELAS", styles['Heading3']))
    elements.append(Spacer(1, 8))
    class_data = [['Kelas', 'Bilangan Pelajar']]
    grand_total = 0
    for cls in sorted(data.get('students_by_class', {}).keys()):
        n = len(data['students_by_class'][cls])
        class_data.append([cls, str(n)])
        grand_total += n
    class_data.append(['JUMLAH', str(grand_total)])
    t = Table(class_data, colWidths=[8*cm, 4*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#dbeafe')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 15))

    elements.append(Paragraph("SENARAI MATA PELAJARAN", styles['Heading3']))
    elements.append(Spacer(1, 8))
    subj_data = [['Bil', 'Kod', 'Mata Pelajaran', 'Kategori']]
    idx = 1
    for cat in ['bahasa', 'sains', 'kemanusiaan', 'vokasional']:
        for s in data.get('subject_headcount', {}).get(cat, []):
            subj_data.append([str(idx), s.get('sheet', ''), s.get('name', ''), cat.upper()])
            idx += 1
    t = Table(subj_data, colWidths=[1*cm, 1.5*cm, 8*cm, 3*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t)

    doc.build(elements)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='spm_ringkasan_keseluruhan.pdf', mimetype='application/pdf')

@app.route('/print/students/<class_name>')
def print_class(class_name):
    data = load_data()
    si = data.get('school_info', {})
    students = data.get('students_by_class', {}).get(class_name, [])
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm)
    elements = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('T', parent=styles['Heading1'], fontSize=14, textColor=colors.HexColor('#1e40af'), spaceAfter=15, alignment=1)

    elements.append(Paragraph(f"SENARAI NAMA MURID - {class_name}", title_style))
    elements.append(Paragraph(si.get('school_name', ''), ParagraphStyle('S', parent=styles['Normal'], fontSize=10, alignment=1, spaceAfter=15)))
    
    tbl = [['Bil', 'Nama Pelajar', 'Kelas']]
    for s in students:
        tbl.append([str(s.get('bil', '')), s.get('name', ''), s.get('class', class_name)])
    t = Table(tbl, colWidths=[1.5*cm, 12*cm, 4*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
    ]))
    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    safe_name = class_name.replace(' ', '_')
    return send_file(buffer, as_attachment=True, download_name=f'senarai_{safe_name}.pdf', mimetype='application/pdf')

@app.route('/print/all-students')
def print_all_students():
    data = load_data()
    si = data.get('school_info', {})
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm)
    elements = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('T', parent=styles['Heading1'], fontSize=14, textColor=colors.HexColor('#1e40af'), spaceAfter=15, alignment=1)

    elements.append(Paragraph("SENARAI NAMA MURID 2026", title_style))
    elements.append(Paragraph(si.get('school_name', ''), ParagraphStyle('S', parent=styles['Normal'], fontSize=10, alignment=1, spaceAfter=15)))

    for cls in sorted(data.get('students_by_class', {}).keys()):
        students = data['students_by_class'][cls]
        elements.append(Paragraph(f"KELAS: {cls} ({len(students)} orang)", styles['Heading3']))
        elements.append(Spacer(1, 5))
        tbl = [['Bil', 'Nama Pelajar']]
        for s in students:
            tbl.append([str(s.get('bil', '')), s.get('name', '')])
        t = Table(tbl, colWidths=[1.5*cm, 15*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 10))

    doc.build(elements)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='senarai_nama_murid_2026.pdf', mimetype='application/pdf')

@app.route('/print/headcount')
def print_headcount():
    data = load_data()
    si = data.get('school_info', {})
    form_filter = request.args.get('form', '1')
    exam_filter = request.args.get('exam', 'UAT')
    fn = int(form_filter)
    is_upper = fn >= 4
    grade_cols = ['A+', 'A', 'A-', 'B+', 'B', 'C+', 'C', 'D', 'E', 'G'] if is_upper else ['A', 'B', 'C', 'D', 'E', 'F']
    exam_labels_local = {'UAT': 'UJIAN AWAL TAHUN', 'PPT': 'PEPERIKSAAN PERTENGAHAN TAHUN', 'PAT': 'PEPERIKSAAN AKHIR TAHUN'}
    exam_label = exam_labels_local.get(exam_filter, exam_filter)

    uat = data.get('uat_data', {})
    form_classes = sorted([c for c in uat.keys() if get_form_number(c) == fn])

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=0.6*cm, bottomMargin=0.6*cm,
                            leftMargin=0.8*cm, rightMargin=0.8*cm)
    elements = []
    styles = getSampleStyleSheet()
    ts = ParagraphStyle('T', parent=styles['Normal'], fontSize=7, leading=9)
    tb = ParagraphStyle('TB', parent=styles['Normal'], fontSize=7, leading=9, fontName='Helvetica-Bold')
    title_s = ParagraphStyle('Title', parent=styles['Heading2'], fontSize=11, alignment=1,
                             textColor=colors.HexColor('#1e3a5f'))

    school_name = si.get('school_name', 'SMK TUANKU LAILATUL SHAHREEN')

    for cls in form_classes:
        cls_students = uat.get(cls, [])
        actual_subjects = {}
        for s in cls_students:
            for sname, sd in s.get('subjects', {}).items():
                if sd.get('grade', '') or sd.get('mark', ''):
                    actual_subjects[sname] = True
        subj_order = cls_students[0].get('subject_order', []) if cls_students else []
        subjects_list = [s for s in subj_order if s in actual_subjects]

        elements.append(Paragraph(f"HEADCOUNT MATA PELAJARAN — {cls}", title_s))
        elements.append(Paragraph(f"{exam_label} 2026 — {school_name}", ParagraphStyle('Sch',
                        parent=styles['Normal'], fontSize=8, alignment=1, spaceAfter=6)))

        hdr = [Paragraph('<b>Mata Pelajaran</b>', tb), Paragraph('<b>Dftr</b>', tb),
               Paragraph('<b>Hdir</b>', tb)]
        for g in grade_cols:
            hdr.append(Paragraph(f'<b>{g}</b>', tb))
        hdr.extend([Paragraph('<b>TH</b>', tb), Paragraph('<b>Lulus</b>', tb),
                    Paragraph('<b>%L</b>', tb), Paragraph('<b>Gagal</b>', tb),
                    Paragraph('<b>%G</b>', tb), Paragraph('<b>GPMP</b>', tb)])

        gc = len(grade_cols)
        col_w = [5*cm, 0.8*cm, 0.8*cm] + [0.7*cm]*gc + [0.7*cm, 0.9*cm, 1*cm, 0.9*cm, 1*cm, 1*cm]
        rows = [hdr]

        if is_upper:
            gp_map = {'A+': 1, 'A': 2, 'A-': 3, 'B+': 4, 'B': 5, 'C+': 6, 'C': 7, 'D': 8, 'E': 9, 'G': 0}
        else:
            gp_map = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6}

        for subj in subjects_list:
            grade_dist = {g: 0 for g in grade_cols}
            th_count = 0; hadir = 0
            for s in cls_students:
                sd = s.get('subjects', {}).get(subj, {})
                g = sd.get('grade', ''); m = sd.get('mark', '')
                if g == 'TH' or m == 'TH':
                    th_count += 1
                elif g in grade_dist:
                    grade_dist[g] += 1; hadir += 1
                elif g:
                    hadir += 1
            total_graded = sum(grade_dist.values())
            lulus = sum(grade_dist[g] for g in grade_cols if g not in ('F', 'G'))
            gagal = total_graded - lulus
            total_gp = sum(grade_dist[g] * gp_map.get(g, 0) for g in grade_cols)
            gpmp = (total_gp / total_graded) if total_graded > 0 else 0
            lulus_pct = (lulus / total_graded * 100) if total_graded > 0 else 0
            gagal_pct = (gagal / total_graded * 100) if total_graded > 0 else 0

            row = [Paragraph(subj, ts), Paragraph(str(len(cls_students)), ts),
                   Paragraph(str(hadir), ts)]
            for g in grade_cols:
                row.append(Paragraph(str(grade_dist[g]) if grade_dist[g] > 0 else '-', ts))
            row.extend([
                Paragraph(str(th_count) if th_count > 0 else '-', ts),
                Paragraph(str(lulus), tb), Paragraph(f'{lulus_pct:.1f}%', ts),
                Paragraph(str(gagal) if gagal > 0 else '-', ts),
                Paragraph(f'{gagal_pct:.1f}%' if gagal > 0 else '-', ts),
                Paragraph(f'{gpmp:.2f}', tb),
            ])
            rows.append(row)

        t = Table(rows, colWidths=col_w, repeatRows=1)
        style_cmds = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#cbd5e1')),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]
        for ri in range(1, len(rows)):
            if ri % 2 == 0:
                style_cmds.append(('BACKGROUND', (0, ri), (-1, ri), colors.HexColor('#f8fafc')))
        t.setStyle(TableStyle(style_cmds))
        elements.append(t)
        elements.append(PageBreak())

    if elements and isinstance(elements[-1], PageBreak):
        elements.pop()

    doc.build(elements)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True,
                     download_name=f'headcount_T{form_filter}_{exam_filter}.pdf', mimetype='application/pdf')

## ============================================================
## MARKS ENTRY, REPORT CARDS & TINGKATAN SUMMARY (Form 1-3)
## ============================================================

GRADE_TABLE = [
    (90, 'A+', 1), (80, 'A', 2), (70, 'A-', 3),
    (65, 'B+', 4), (60, 'B', 5), (55, 'C+', 6),
    (50, 'C', 7), (45, 'D', 8), (40, 'E', 9), (0, 'G', 0)
]

def calc_grade(mark):
    if mark is None or mark == '':
        return '', 0
    try:
        m = float(mark)
    except (ValueError, TypeError):
        return '', 0
    for threshold, grade, point in GRADE_TABLE:
        if m >= threshold:
            return grade, point
    return 'G', 0

def get_class_type(class_name):
    parts = class_name.split(' ', 1)
    return parts[1] if len(parts) > 1 else class_name

def get_form_number(class_name):
    parts = class_name.split(' ', 1)
    try:
        return int(parts[0])
    except (ValueError, IndexError):
        return 0

def get_subjects_for_class(data, class_name):
    # First try per-class subjects from UAT extraction (most accurate)
    fn = str(get_form_number(class_name))
    csbf = data.get('class_subjects_by_form', {})
    if fn in csbf and class_name in csbf[fn]:
        return csbf[fn][class_name]
    # Fallback to generic config
    cls_type = get_class_type(class_name)
    config = data.get('class_subjects_config', {})
    return config.get(cls_type, [])

@app.route('/marks')
def marks_page():
    data = load_data()
    form_filter = request.args.get('form', '1')
    exam_filter = request.args.get('exam', 'UAT')
    fn = int(form_filter) if form_filter.isdigit() else 1
    uat = data.get('uat_data', {})
    classes = {}
    for cls in sorted(uat.keys()):
        f = get_form_number(cls)
        if f in [1, 2, 3, 4, 5]:
            classes.setdefault(str(f), []).append(cls)
    current_exams = EXAM_LIST_F5 if fn == 5 else EXAM_LIST
    return render_template('marks.html', data=data, classes=classes, form_filter=form_filter,
                           exam_filter=exam_filter, exams=current_exams, exam_labels=EXAM_LABELS)

@app.route('/marks/entry/<class_name>')
def marks_entry(class_name):
    data = load_data()
    exam_filter = request.args.get('exam', 'UAT')
    fn = get_form_number(class_name)
    uat = data.get('uat_data', {})
    cls_students = uat.get(class_name, [])

    # Get actual subjects this class takes from uat_data
    actual_subjects = {}
    for s in cls_students:
        for sname, sd in s.get('subjects', {}).items():
            if sd.get('grade', '') or sd.get('mark', ''):
                actual_subjects[sname] = True
    subj_order = cls_students[0].get('subject_order', []) if cls_students else []
    subjects = [sn for sn in subj_order if sn in actual_subjects]

    # Build marks dict from uat_data (pre-fill from Excel)
    marks = {}
    for s in cls_students:
        student_name = s.get('name', '')
        marks[student_name] = {}
        marks[student_name]['UAT'] = {}
        for sname, sd in s.get('subjects', {}).items():
            m = sd.get('mark', '')
            if isinstance(m, (int, float)):
                marks[student_name]['UAT'][sname] = m
            elif m == 'TH':
                marks[student_name]['UAT'][sname] = 'TH'

    # Also merge any saved marks_data (for PPT/PAT/PSPM entered manually)
    saved_marks = data.get('marks_data', {}).get(class_name, {})
    for sname, sexams in saved_marks.items():
        if sname not in marks:
            marks[sname] = {}
        for ex, subj_marks in sexams.items():
            if ex not in marks[sname]:
                marks[sname][ex] = {}
            marks[sname][ex].update(subj_marks)

    students = [{'name': s.get('name', ''), 'ic': s.get('ic', '')} for s in cls_students]
    current_exams = EXAM_LIST_F5 if fn == 5 else EXAM_LIST
    return render_template('marks_entry.html', data=data, class_name=class_name,
                           students=students, subjects=subjects, exams=current_exams,
                           exam_filter=exam_filter, marks=marks, exam_labels=EXAM_LABELS)

@app.route('/marks/save', methods=['POST'])
def marks_save():
    data = load_data()
    form = request.json
    class_name = form.get('class_name', '')
    exam = form.get('exam', '')
    marks_input = form.get('marks', {})
    if class_name not in data.get('marks_data', {}):
        data.setdefault('marks_data', {})[class_name] = {}
    for student_name, subject_marks in marks_input.items():
        if student_name not in data['marks_data'][class_name]:
            data['marks_data'][class_name][student_name] = {}
        if exam not in data['marks_data'][class_name][student_name]:
            data['marks_data'][class_name][student_name][exam] = {}
        for subj, mark_val in subject_marks.items():
            data['marks_data'][class_name][student_name][exam][subj] = mark_val
    save_data(data)
    return jsonify({'success': True, 'message': f'Markah {class_name} ({exam}) berjaya disimpan!'})

@app.route('/report-cards')
def report_cards_page():
    data = load_data()
    form_filter = request.args.get('form', '1')
    class_filter = request.args.get('class', '')
    classes = {}
    for cls in sorted(data.get('students_by_class', {}).keys()):
        fn = get_form_number(cls)
        if fn in [1, 2, 3, 4, 5]:
            classes.setdefault(str(fn), []).append(cls)
    return render_template('report_cards.html', data=data, classes=classes,
                           form_filter=form_filter, class_filter=class_filter)

@app.route('/report-card/<class_name>/<int:student_idx>')
def report_card_student(class_name, student_idx):
    data = load_data()
    students = data.get('students_by_class', {}).get(class_name, [])
    if student_idx >= len(students):
        return "Pelajar tidak dijumpai", 404
    student = students[student_idx]
    subjects = get_subjects_for_class(data, class_name)
    fn = get_form_number(class_name)
    exams = EXAM_LIST_F5 if fn == 5 else EXAM_LIST
    marks = data.get('marks_data', {}).get(class_name, {}).get(student['name'], {})
    results = []
    for subj in subjects:
        row = {'name': subj, 'exams': {}}
        for ex in exams:
            m = marks.get(ex, {}).get(subj, '')
            grade, point = calc_grade(m)
            row['exams'][ex] = {'mark': m, 'grade': grade, 'point': point}
        results.append(row)
    totals = {}
    for ex in exams:
        total_marks = 0
        total_points = 0
        count = 0
        for r in results:
            em = r['exams'].get(ex, {})
            if em.get('mark') not in (None, ''):
                try:
                    total_marks += float(em['mark'])
                    total_points += em['point']
                    count += 1
                except (ValueError, TypeError):
                    pass
        avg = round(total_marks / count, 2) if count > 0 else 0
        gpa = round(total_points / count, 2) if count > 0 else 0
        grade, _ = calc_grade(avg)
        totals[ex] = {'total_marks': total_marks, 'avg': avg, 'grade': grade,
                       'total_points': total_points, 'gpa': gpa, 'count': count}
    return render_template('report_card_student.html', data=data, student=student,
                           class_name=class_name, student_idx=student_idx,
                           subjects=subjects, exams=exams, results=results, totals=totals)

@app.route('/print/report-card/<class_name>/<int:student_idx>')
def print_report_card(class_name, student_idx):
    data = load_data()
    si = data.get('school_info', {})
    students = data.get('students_by_class', {}).get(class_name, [])
    if student_idx >= len(students):
        return "Pelajar tidak dijumpai", 404
    student = students[student_idx]
    subjects = get_subjects_for_class(data, class_name)
    fn = get_form_number(class_name)
    exams = EXAM_LIST_F5 if fn == 5 else EXAM_LIST
    marks = data.get('marks_data', {}).get(class_name, {}).get(student['name'], {})
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm,
                            leftMargin=1.5*cm, rightMargin=1.5*cm)
    elements = []
    styles = getSampleStyleSheet()
    title_s = ParagraphStyle('T', parent=styles['Heading1'], fontSize=13,
                             textColor=colors.HexColor('#1e40af'), spaceAfter=5, alignment=1)
    sub_s = ParagraphStyle('S', parent=styles['Normal'], fontSize=9, alignment=1, spaceAfter=3)
    elements.append(Paragraph(si.get('school_name', 'SMK TUANKU LAILATUL SHAHREEN'), title_s))
    elements.append(Paragraph(si.get('state', 'JABATAN PENDIDIKAN NEGERI PERLIS'), sub_s))
    elements.append(Paragraph("KAD LAPORAN PELAJAR", ParagraphStyle('K', parent=styles['Heading2'],
                              fontSize=12, alignment=1, spaceAfter=10, textColor=colors.HexColor('#1e40af'))))
    info_tbl = [
        ['Nama Pelajar:', student.get('name', ''), 'Kelas:', class_name],
        ['Tingkatan:', student.get('form', ''), 'Tahun:', str(si.get('exam_year', 2026))],
    ]
    t = Table(info_tbl, colWidths=[2.5*cm, 7*cm, 2*cm, 5*cm])
    t.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f1f5f9')),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 10))
    hdr = ['Bil', 'Mata Pelajaran']
    for ex in exams:
        hdr.extend([f'{ex}\nMarkah', f'{ex}\nGred'])
    tbl_data = [hdr]
    for i, subj in enumerate(subjects):
        row = [str(i + 1), subj]
        for ex in exams:
            m = marks.get(ex, {}).get(subj, '')
            grade, _ = calc_grade(m)
            row.extend([str(m) if m != '' else '', grade])
        tbl_data.append(row)
    summary_row = ['', 'PURATA / GPA']
    for ex in exams:
        total_m = 0
        cnt = 0
        total_p = 0
        for subj in subjects:
            m = marks.get(ex, {}).get(subj, '')
            if m not in (None, ''):
                try:
                    total_m += float(m)
                    _, p = calc_grade(m)
                    total_p += p
                    cnt += 1
                except (ValueError, TypeError):
                    pass
        avg = round(total_m / cnt, 1) if cnt > 0 else ''
        gpa = round(total_p / cnt, 2) if cnt > 0 else ''
        summary_row.extend([str(avg), str(gpa)])
    tbl_data.append(summary_row)
    n_exam_cols = len(exams) * 2
    col_w = [0.8*cm, 4.5*cm] + [1.4*cm] * n_exam_cols
    t = Table(tbl_data, colWidths=col_w)
    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#dbeafe')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]
    for row_idx in range(1, len(tbl_data) - 1):
        for ex_idx in range(len(exams)):
            grade_col = 3 + ex_idx * 2
            cell_val = tbl_data[row_idx][grade_col] if grade_col < len(tbl_data[row_idx]) else ''
            if cell_val in ('A+', 'A', 'A-'):
                style_cmds.append(('TEXTCOLOR', (grade_col, row_idx), (grade_col, row_idx), colors.HexColor('#059669')))
            elif cell_val in ('E', 'G'):
                style_cmds.append(('TEXTCOLOR', (grade_col, row_idx), (grade_col, row_idx), colors.HexColor('#dc2626')))
    t.setStyle(TableStyle(style_cmds))
    elements.append(t)
    elements.append(Spacer(1, 15))
    elements.append(Paragraph("_________________________", ParagraphStyle('sig', parent=styles['Normal'], fontSize=9, alignment=2)))
    elements.append(Paragraph("Tandatangan Pengetua", ParagraphStyle('sig2', parent=styles['Normal'], fontSize=8, alignment=2)))
    doc.build(elements)
    buffer.seek(0)
    safe = student.get('name', 'student').replace(' ', '_')
    return send_file(buffer, as_attachment=True, download_name=f'kad_laporan_{safe}.pdf', mimetype='application/pdf')

@app.route('/print/report-cards-class/<class_name>')
def print_report_cards_class(class_name):
    data = load_data()
    si = data.get('school_info', {})
    students = data.get('students_by_class', {}).get(class_name, [])
    subjects = get_subjects_for_class(data, class_name)
    exams = data.get('lower_form_exams', ['TOV', 'OTI1', 'PPT', 'PAT'])
    all_marks = data.get('marks_data', {}).get(class_name, {})
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm,
                            leftMargin=1.5*cm, rightMargin=1.5*cm)
    elements = []
    styles = getSampleStyleSheet()
    title_s = ParagraphStyle('T', parent=styles['Heading1'], fontSize=13,
                             textColor=colors.HexColor('#1e40af'), spaceAfter=5, alignment=1)
    sub_s = ParagraphStyle('S', parent=styles['Normal'], fontSize=9, alignment=1, spaceAfter=3)
    for s_idx, student in enumerate(students):
        if s_idx > 0:
            elements.append(PageBreak())
        elements.append(Paragraph(si.get('school_name', 'SMK TUANKU LAILATUL SHAHREEN'), title_s))
        elements.append(Paragraph("KAD LAPORAN PELAJAR", sub_s))
        elements.append(Spacer(1, 5))
        info_tbl = [
            ['Nama:', student.get('name', ''), 'Kelas:', class_name],
            ['Tingkatan:', student.get('form', ''), 'Tahun:', str(si.get('exam_year', 2026))],
        ]
        t = Table(info_tbl, colWidths=[2*cm, 7.5*cm, 2*cm, 5*cm])
        t.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 8), ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f1f5f9')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 8))
        marks = all_marks.get(student['name'], {})
        hdr = ['Bil', 'Mata Pelajaran']
        for ex in exams:
            hdr.extend([f'{ex}\nMarkah', f'{ex}\nGred'])
        tbl_data = [hdr]
        for i, subj in enumerate(subjects):
            row = [str(i + 1), subj]
            for ex in exams:
                m = marks.get(ex, {}).get(subj, '')
                grade, _ = calc_grade(m)
                row.extend([str(m) if m != '' else '', grade])
            tbl_data.append(row)
        n_exam_cols = len(exams) * 2
        col_w = [0.7*cm, 4*cm] + [1.3*cm] * n_exam_cols
        t = Table(tbl_data, colWidths=col_w)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    safe = class_name.replace(' ', '_')
    return send_file(buffer, as_attachment=True, download_name=f'kad_laporan_{safe}.pdf', mimetype='application/pdf')

@app.route('/tingkatan-summary')
def tingkatan_summary():
    data = load_data()
    form_filter = request.args.get('form', '1')
    exam_filter = request.args.get('exam', 'UAT')
    fn = int(form_filter)
    exams = EXAM_LIST_F5 if fn == 5 else EXAM_LIST
    form_classes = [cls for cls in sorted(data.get('students_by_class', {}).keys())
                    if get_form_number(cls) == fn]
    summary = []
    for cls in form_classes:
        students = data.get('students_by_class', {}).get(cls, [])
        subjects = get_subjects_for_class(data, cls)
        cls_marks = data.get('marks_data', {}).get(cls, {})
        subj_stats = []
        for subj in subjects:
            marks_list = []
            grade_dist = {}
            for s in students:
                m = cls_marks.get(s['name'], {}).get(exam_filter, {}).get(subj, '')
                if m not in (None, ''):
                    try:
                        marks_list.append(float(m))
                        g, _ = calc_grade(m)
                        grade_dist[g] = grade_dist.get(g, 0) + 1
                    except (ValueError, TypeError):
                        pass
            avg = round(sum(marks_list) / len(marks_list), 2) if marks_list else 0
            lulus = sum(1 for m in marks_list if m >= 40)
            subj_stats.append({
                'name': subj, 'count': len(marks_list), 'avg': avg,
                'highest': max(marks_list) if marks_list else 0,
                'lowest': min(marks_list) if marks_list else 0,
                'lulus': lulus,
                'lulus_pct': round(lulus / len(marks_list) * 100, 1) if marks_list else 0,
                'grade_dist': grade_dist
            })
        summary.append({
            'class_name': cls, 'total_students': len(students),
            'subjects': subj_stats
        })
    all_subjects = set()
    for s in summary:
        for subj in s['subjects']:
            all_subjects.add(subj['name'])
    return render_template('tingkatan_summary.html', data=data, form_filter=form_filter,
                           exam_filter=exam_filter, exams=exams, summary=summary,
                           all_subjects=sorted(all_subjects))

@app.route('/print/tingkatan-summary/<int:form_num>/<exam>')
def print_tingkatan_summary(form_num, exam):
    data = load_data()
    si = data.get('school_info', {})
    form_classes = [cls for cls in sorted(data.get('students_by_class', {}).keys())
                    if get_form_number(cls) == form_num]
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=0.5*cm, bottomMargin=0.5*cm)
    elements = []
    styles = getSampleStyleSheet()
    title_s = ParagraphStyle('T', parent=styles['Heading1'], fontSize=13,
                             textColor=colors.HexColor('#1e40af'), spaceAfter=8, alignment=1)
    elements.append(Paragraph(f"RUMUSAN TINGKATAN {form_num} - {exam}", title_s))
    elements.append(Paragraph(si.get('school_name', ''), ParagraphStyle('S', parent=styles['Normal'],
                              fontSize=9, alignment=1, spaceAfter=10)))
    for cls in form_classes:
        students = data.get('students_by_class', {}).get(cls, [])
        subjects = get_subjects_for_class(data, cls)
        cls_marks = data.get('marks_data', {}).get(cls, {})
        elements.append(Paragraph(f"{cls} ({len(students)} pelajar)", styles['Heading3']))
        elements.append(Spacer(1, 4))
        hdr = ['Bil', 'Nama Pelajar'] + [Paragraph(s[:12], ParagraphStyle('h', fontSize=6)) for s in subjects] + ['Jumlah', 'Purata', 'Gred']
        tbl_data = [hdr]
        for i, s in enumerate(students):
            row = [str(i + 1), Paragraph(s['name'], ParagraphStyle('n', fontSize=6))]
            total = 0
            cnt = 0
            for subj in subjects:
                m = cls_marks.get(s['name'], {}).get(exam, {}).get(subj, '')
                row.append(str(m) if m != '' else '')
                if m not in (None, ''):
                    try:
                        total += float(m)
                        cnt += 1
                    except (ValueError, TypeError):
                        pass
            avg = round(total / cnt, 1) if cnt > 0 else 0
            grade, _ = calc_grade(avg)
            row.extend([str(round(total, 1)) if cnt > 0 else '', str(avg) if cnt > 0 else '', grade])
            tbl_data.append(row)
        n_subj = len(subjects)
        col_w = [0.6*cm, 3*cm] + [1.2*cm] * n_subj + [1.2*cm, 1.2*cm, 1*cm]
        t = Table(tbl_data, colWidths=col_w)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 0), (-1, -1), 6),
            ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 10))
    doc.build(elements)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True,
                     download_name=f'rumusan_tingkatan_{form_num}_{exam}.pdf', mimetype='application/pdf')

## ============================================================
## RUMUSAN (Ranking + Analisis per Form, matching Excel format)
## ============================================================

GRADE_ORDER_LOWER = ['A', 'B', 'C', 'D', 'E', 'F']
GRADE_ORDER_UPPER = ['A+', 'A', 'A-', 'B+', 'B', 'C+', 'C', 'D', 'E', 'G']
GRADE_GP_LOWER = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6}
GRADE_GP_UPPER = {'A+': 1, 'A': 2, 'A-': 3, 'B+': 4, 'B': 5, 'C+': 6, 'C': 7, 'D': 8, 'E': 9, 'G': 0}

@app.route('/rumusan')
def rumusan_page():
    data = load_data()
    form_filter = request.args.get('form', '1')
    exam_filter = request.args.get('exam', 'UAT')
    tab = request.args.get('tab', 'ranking')
    fn = int(form_filter)
    is_upper = fn >= 4
    grade_cols = GRADE_ORDER_UPPER if is_upper else GRADE_ORDER_LOWER

    uat = data.get('uat_data', {})
    guru_map = data.get('guru_kelas', {})
    subject_maps = data.get('subject_maps', {})
    subj_map = subject_maps.get(form_filter, {})
    subjects_short = list(subj_map.keys()) if subj_map else []
    subjects_full = list(subj_map.values()) if subj_map else []

    # Gather all students for this form
    form_classes = sorted([c for c in uat.keys() if get_form_number(c) == fn])
    all_students = []
    for cls in form_classes:
        all_students.extend(uat.get(cls, []))

    # --- Ranking tab ---
    ranking = sorted(
        [s for s in all_students if s.get('gp', 99) < 90],
        key=lambda x: (x['gp'], -(x.get('jumlah_markah', 0) if isinstance(x.get('jumlah_markah'), (int, float)) else 0))
    )

    # --- Analisis Pencapaian Mengikut Kelas tab ---
    analisis_kelas = []
    for cls in form_classes:
        cls_students = uat.get(cls, [])
        grade_counts = {g: 0 for g in grade_cols}
        th_count = 0
        total_gp = 0
        total_gp_count = 0
        for s in cls_students:
            for subj_name, sd in s.get('subjects', {}).items():
                g = sd.get('grade', '')
                if g == 'TH':
                    th_count += 1
                elif g in grade_counts:
                    grade_counts[g] += 1
                gp_val = sd.get('gp')
                if gp_val is not None and g != 'TH':
                    total_gp += gp_val
                    total_gp_count += 1
        total_grades = sum(grade_counts.values())
        grades_info = {}
        for g in grade_cols:
            cnt = grade_counts[g]
            pct = (cnt / total_grades * 100) if total_grades > 0 else 0
            grades_info[g] = {'count': cnt, 'pct': pct}
        gps = (total_gp / total_gp_count) if total_gp_count > 0 else 0
        analisis_kelas.append({
            'class': cls, 'grades': grades_info, 'th': th_count, 'gps': gps
        })

    # --- Analisis Penuh tab ---
    analisis_penuh = []
    pass_grades_lower = {'A', 'B', 'C', 'D', 'E'}
    pass_grades_upper = {'A+', 'A', 'A-', 'B+', 'B', 'C+', 'C', 'D', 'E'}
    a_grades_lower = {'A'}
    a_grades_upper = {'A+', 'A', 'A-'}
    for cls in form_classes:
        cls_students = uat.get(cls, [])
        total = len(cls_students)
        hadir = 0; semua_a = 0; lulus = 0; gagal = 0
        total_gp = 0; gp_count = 0
        for s in cls_students:
            subjs = s.get('subjects', {})
            active = [sd for sd in subjs.values() if sd.get('grade', '') != '' and sd.get('grade', '') != 'TH']
            if not active:
                continue
            hadir += 1
            grades = [sd.get('grade', '') for sd in active]
            a_set = a_grades_upper if is_upper else a_grades_lower
            p_set = pass_grades_upper if is_upper else pass_grades_lower
            if all(g in a_set for g in grades):
                semua_a += 1
            if all(g in p_set for g in grades):
                lulus += 1
            else:
                gagal += 1
            if s.get('gp', 99) < 90:
                total_gp += s['gp']
                gp_count += 1
        gps = (total_gp / gp_count) if gp_count > 0 else 0
        analisis_penuh.append({
            'class': cls, 'total': total, 'hadir': hadir,
            'semua_a': semua_a, 'semua_a_pct': (semua_a / total * 100) if total else 0,
            'lulus': lulus, 'lulus_pct': (lulus / total * 100) if total else 0,
            'gagal': gagal, 'gagal_pct': (gagal / total * 100) if total else 0,
            'gps': gps
        })

    exam_labels_local = {
        'UAT': 'UJIAN AWAL TAHUN', 'PPT': 'PEPERIKSAAN PERTENGAHAN TAHUN',
        'PAT': 'PEPERIKSAAN AKHIR TAHUN',
    }
    return render_template('rumusan.html', data=data, form_filter=form_filter,
                           exam_filter=exam_filter, tab=tab,
                           exam_label=exam_labels_local.get(exam_filter, exam_filter),
                           exams=(EXAM_LIST_F5 if fn == 5 else EXAM_LIST), exam_labels=EXAM_LABELS,
                           grade_cols=grade_cols, ranking=ranking,
                           analisis_kelas=analisis_kelas, analisis_penuh=analisis_penuh,
                           subjects_short=subjects_short, subjects_full=subjects_full,
                           guru_map=guru_map)

@app.route('/print/rumusan/<form_num>')
def print_rumusan(form_num):
    data = load_data()
    exam_filter = request.args.get('exam', 'UAT')
    fn = int(form_num)
    is_upper = fn >= 4
    grade_cols = GRADE_ORDER_UPPER if is_upper else GRADE_ORDER_LOWER

    uat = data.get('uat_data', {})
    guru_map = data.get('guru_kelas', {})
    subject_maps = data.get('subject_maps', {})
    subj_map = subject_maps.get(str(fn), {})
    subjects_short = list(subj_map.keys()) if subj_map else []
    subjects_full = list(subj_map.values()) if subj_map else []

    form_classes = sorted([c for c in uat.keys() if get_form_number(c) == fn])
    all_students = []
    for cls in form_classes:
        all_students.extend(uat.get(cls, []))
    ranking = sorted(
        [s for s in all_students if s.get('gp', 99) < 90],
        key=lambda x: (x['gp'], -(x.get('jumlah_markah', 0) if isinstance(x.get('jumlah_markah'), (int, float)) else 0))
    )

    si = data.get('school_info', {})
    school_name = si.get('school_name', 'SMK TUANKU LAILATUL SHAHREEN')
    exam_labels_local = {'UAT': 'UJIAN AWAL TAHUN', 'PPT': 'PEPERIKSAAN PERTENGAHAN TAHUN', 'PAT': 'PEPERIKSAAN AKHIR TAHUN'}
    exam_label = exam_labels_local.get(exam_filter, exam_filter)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=0.8*cm, bottomMargin=0.8*cm,
                            leftMargin=0.8*cm, rightMargin=0.8*cm)
    elements = []
    styles = getSampleStyleSheet()
    ts = ParagraphStyle('T', parent=styles['Normal'], fontSize=6, leading=8)
    tb = ParagraphStyle('TB', parent=styles['Normal'], fontSize=6, leading=8, fontName='Helvetica-Bold')
    title_s = ParagraphStyle('Title', parent=styles['Heading2'], fontSize=10, alignment=1,
                             textColor=colors.HexColor('#1e3a5f'))

    elements.append(Paragraph(f"RUMUSAN TINGKATAN {form_num} — {exam_label} 2026", title_s))
    elements.append(Paragraph(school_name, ParagraphStyle('Sch', parent=styles['Normal'],
                              fontSize=8, alignment=1, fontName='Helvetica-Bold')))
    elements.append(Spacer(1, 8))

    # Build header
    hdr = [Paragraph('<b>KDT</b>', tb), Paragraph('<b>Nama Pelajar</b>', tb),
           Paragraph('<b>Kelas</b>', tb)]
    for sc in subjects_short:
        hdr.append(Paragraph(f'<b>{sc}</b>', tb))
    hdr.extend([Paragraph('<b>Jum</b>', tb), Paragraph('<b>%</b>', tb),
                Paragraph('<b>GP</b>', tb), Paragraph('<b>KDK</b>', tb),
                Paragraph('<b>Guru Kelas</b>', tb)])

    subj_count = len(subjects_short)
    col_w = [0.9*cm, 5.5*cm, 2*cm] + [0.7*cm]*subj_count + [1*cm, 0.9*cm, 0.9*cm, 1.1*cm, 4*cm]
    rows = [hdr]
    for s in ranking:
        row = [
            Paragraph(str(s.get('kdt', '')), ts),
            Paragraph(s.get('name', ''), ts),
            Paragraph(s.get('class', ''), ts),
        ]
        for sf in subjects_full:
            sd = s.get('subjects', {}).get(sf, {})
            m = sd.get('mark', '')
            mstr = str(int(m)) if isinstance(m, (int, float)) else str(m) if m else ''
            row.append(Paragraph(mstr, ts))
        jum = s.get('jumlah_markah', '')
        jstr = str(int(jum)) if isinstance(jum, (int, float)) else str(jum or '')
        pur = s.get('purata', '')
        pstr = f"{float(pur):.1f}" if isinstance(pur, (int, float)) else ''
        gstr = f"{s['gp']:.2f}" if s.get('gp', 99) < 90 else '-'
        row.extend([
            Paragraph(jstr, ts), Paragraph(pstr, ts),
            Paragraph(f'<b>{gstr}</b>', tb),
            Paragraph(str(s.get('kdk', '')), ts),
            Paragraph(guru_map.get(s.get('class', ''), ''), ts),
        ])
        rows.append(row)

    t = Table(rows, colWidths=col_w, repeatRows=1)
    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#cbd5e1')),
        ('FONTSIZE', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]
    for ri in range(1, len(rows)):
        if ri % 2 == 0:
            style_cmds.append(('BACKGROUND', (0, ri), (-1, ri), colors.HexColor('#f8fafc')))
    t.setStyle(TableStyle(style_cmds))
    elements.append(t)

    doc.build(elements)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True,
                     download_name=f'rumusan_T{form_num}_{exam_filter}.pdf', mimetype='application/pdf')

## ============================================================
## SLIP PEPERIKSAAN (UAT Data - Form 1-5)
## ============================================================

TAKSIRAN_MAP = {
    'A+': 'CEMERLANG', 'A': 'CEMERLANG', 'A-': 'KEPUJIAN TINGGI',
    'B+': 'KEPUJIAN ATAS', 'B': 'KEPUJIAN', 'C+': 'MEMUASKAN TINGGI',
    'C': 'BAIK', 'D': 'MEMUASKAN', 'E': 'MENCAPAI TAHAP MINIMUM',
    'F': 'BELUM MENCAPAI TAHAP MINIMUM', 'G': 'GAGAL', 'TH': 'TIDAK HADIR'
}

EXAM_LABELS = {
    'UAT': 'UJIAN AWAL TAHUN',
    'TOV': 'TOV',
    'OTI1': 'OTI 1',
    'PPT': 'PEPERIKSAAN PERTENGAHAN TAHUN',
    'PAT': 'PEPERIKSAAN AKHIR TAHUN',
    'PSPM': 'PEPERIKSAAN PERCUBAAN SPM 2026',
}

EXAM_LIST = ['UAT', 'PPT', 'PAT']
EXAM_LIST_F5 = ['UAT', 'PPT', 'PSPM']

@app.route('/slip-peperiksaan')
def slip_peperiksaan_page():
    data = load_data()
    form_filter = request.args.get('form', '1')
    exam_filter = request.args.get('exam', 'UAT')
    uat = data.get('uat_data', {})
    classes = {}
    for cls in sorted(uat.keys()):
        fn = get_form_number(cls)
        classes.setdefault(str(fn), []).append(cls)
    for cls_name, students in uat.items():
        for idx, s in enumerate(students):
            s['_orig_idx'] = idx
    fn = int(form_filter) if form_filter.isdigit() else 1
    current_exams = EXAM_LIST_F5 if fn == 5 else EXAM_LIST
    return render_template('slip_peperiksaan.html', data=data, classes=classes,
                           form_filter=form_filter, exam_filter=exam_filter,
                           exams=current_exams, exam_labels=EXAM_LABELS)

@app.route('/slip-peperiksaan/<class_name>/<int:student_idx>')
def slip_student(class_name, student_idx):
    data = load_data()
    exam_filter = request.args.get('exam', 'UAT')
    uat = data.get('uat_data', {})
    students = uat.get(class_name, [])
    if student_idx >= len(students):
        return "Pelajar tidak dijumpai", 404
    student = students[student_idx]
    guru = data.get('guru_kelas', {}).get(class_name, '')
    si = data.get('school_info', {})
    return render_template('slip_student.html', data=data, student=student,
                           class_name=class_name, student_idx=student_idx,
                           guru_kelas=guru, school_info=si, taksiran=TAKSIRAN_MAP,
                           total_students=len(students), exam_filter=exam_filter,
                           exam_label=EXAM_LABELS.get(exam_filter, exam_filter))

@app.route('/print/slip/<class_name>/<int:student_idx>')
def print_slip_student(class_name, student_idx):
    data = load_data()
    exam_filter = request.args.get('exam', 'UAT')
    uat = data.get('uat_data', {})
    students = uat.get(class_name, [])
    if student_idx >= len(students):
        return "Pelajar tidak dijumpai", 404
    student = students[student_idx]
    si = data.get('school_info', {})
    guru = data.get('guru_kelas', {}).get(class_name, '')
    exam_label = EXAM_LABELS.get(exam_filter, exam_filter)
    buffer = _build_slip_pdf(data, si, [student], class_name, guru, exam_label)
    safe = student.get('name', 'student').replace(' ', '_')[:30]
    return send_file(buffer, as_attachment=True,
                     download_name=f'slip_{exam_filter}_{safe}.pdf', mimetype='application/pdf')

@app.route('/print/slip-class/<class_name>')
def print_slip_class(class_name):
    data = load_data()
    exam_filter = request.args.get('exam', 'UAT')
    uat = data.get('uat_data', {})
    students = uat.get(class_name, [])
    si = data.get('school_info', {})
    guru = data.get('guru_kelas', {}).get(class_name, '')
    exam_label = EXAM_LABELS.get(exam_filter, exam_filter)
    buffer = _build_slip_pdf(data, si, students, class_name, guru, exam_label)
    safe = class_name.replace(' ', '_')
    return send_file(buffer, as_attachment=True,
                     download_name=f'slip_{exam_filter}_{safe}.pdf', mimetype='application/pdf')

def _build_slip_pdf(data, si, students, class_name, guru_kelas_name, exam_label='UJIAN AWAL TAHUN'):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.6*cm, bottomMargin=0.6*cm,
                            leftMargin=1.2*cm, rightMargin=1.2*cm)
    elements = []
    styles = getSampleStyleSheet()
    school_name = si.get('school_name', 'SMK TUANKU LAILATUL SHAHREEN')
    principal = si.get('principal', 'LILI MARIAM BINTI MOHAMMAD @ MOKHTAR')

    # Styles matching Excel format
    header_title = ParagraphStyle('HdrT', parent=styles['Normal'], fontSize=12,
                                  alignment=1, fontName='Helvetica-Bold', leading=14)
    header_school = ParagraphStyle('HdrS', parent=styles['Normal'], fontSize=10,
                                   alignment=1, fontName='Helvetica-Bold', leading=12)
    header_addr = ParagraphStyle('HdrA', parent=styles['Normal'], fontSize=8,
                                 alignment=1, leading=10)
    exam_title = ParagraphStyle('ExT', parent=styles['Normal'], fontSize=9,
                                alignment=1, fontName='Helvetica-Bold', spaceAfter=4)
    label_s = ParagraphStyle('Lbl', parent=styles['Normal'], fontSize=8, fontName='Helvetica-Bold')
    val_s = ParagraphStyle('Val', parent=styles['Normal'], fontSize=8)
    subj_s = ParagraphStyle('Subj', parent=styles['Normal'], fontSize=7.5, leading=9)
    subj_b = ParagraphStyle('SubjB', parent=styles['Normal'], fontSize=7.5, leading=9, fontName='Helvetica-Bold')
    rumusan_lbl = ParagraphStyle('RumL', parent=styles['Normal'], fontSize=8, fontName='Helvetica-Bold')
    rumusan_val = ParagraphStyle('RumV', parent=styles['Normal'], fontSize=8, fontName='Helvetica-Bold')
    sig_label_s = ParagraphStyle('SigL', parent=styles['Normal'], fontSize=8, alignment=1)
    sig_name_s = ParagraphStyle('SigN', parent=styles['Normal'], fontSize=8, alignment=1, fontName='Helvetica-Bold')
    sig_dots = ParagraphStyle('SigD', parent=styles['Normal'], fontSize=8, alignment=1)

    logo_path = os.path.join(os.path.dirname(__file__), 'static', 'logo.png')
    # Also try the jpg directly
    if not os.path.exists(logo_path):
        logo_path = os.path.join(os.path.dirname(__file__), 'logo smktls.jpg')
    has_logo = os.path.exists(logo_path)

    pw = 17.5*cm  # page width for tables

    for s_idx, student in enumerate(students):
        if s_idx > 0:
            elements.append(PageBreak())

        # ======== HEADER (Logo centered + School Name) ========
        if has_logo:
            logo = Image(logo_path, width=2.2*cm, height=2.2*cm)
            header_content = [
                [Paragraph('', header_title)],  # spacer row
                [logo],
                [Paragraph('SLIP PEPERIKSAAN', header_title)],
                [Paragraph(school_name, header_school)],
                [Paragraph('01000  KANGAR, PERLIS', header_addr)],
            ]
            ht = Table(header_content, colWidths=[pw])
            ht.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
                ('TOPPADDING', (0, 0), (-1, -1), 1),
            ]))
            elements.append(ht)
        else:
            elements.append(Paragraph('SLIP PEPERIKSAAN', header_title))
            elements.append(Paragraph(school_name, header_school))
            elements.append(Paragraph('01000  KANGAR, PERLIS', header_addr))

        elements.append(Spacer(1, 4))
        elements.append(Paragraph(f'{exam_label} 2026', exam_title))
        elements.append(Spacer(1, 4))

        # ======== STUDENT INFO ========
        info_rows = [
            [Paragraph('NAMA  ', label_s), Paragraph(str(student.get('name', '')), val_s)],
            [Paragraph('KELAS  ', label_s), Paragraph(class_name, val_s)],
        ]
        it = Table(info_rows, colWidths=[4.5*cm, pw - 4.5*cm])
        it.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(it)
        elements.append(Spacer(1, 6))

        # ======== SUBJECTS TABLE (matching Excel Row 9+) ========
        subj_hdr = [
            Paragraph('<b>MATAPELAJARAN</b>', subj_b),
            Paragraph('<b>MARKAH</b>', subj_b),
            Paragraph('<b>GRED</b>', subj_b),
            Paragraph('<b>TAKSIRAN GRED</b>', subj_b),
        ]
        subj_rows = [subj_hdr]
        subject_order = student.get('subject_order', [])
        subjects = student.get('subjects', {})
        for subj_name in subject_order:
            sd = subjects.get(subj_name, {})
            mark = sd.get('mark', '')
            grade = sd.get('grade', '')
            if mark == '' and grade == '':
                continue
            taksiran = sd.get('taksiran', TAKSIRAN_MAP.get(str(grade), ''))
            if isinstance(mark, (int, float)):
                mark_str = str(int(mark))
            elif mark == 'TH':
                mark_str = 'TH'
            else:
                mark_str = str(mark) if mark else ''
            subj_rows.append([
                Paragraph(subj_name, subj_s),
                Paragraph(f'<b>{mark_str}</b>', subj_b),
                Paragraph(f'<b>{grade}</b>', subj_b),
                Paragraph(taksiran, subj_s),
            ])

        # No empty padding rows - only show subjects with data

        col_w = [6.5*cm, 2*cm, 1.5*cm, pw - 10*cm]
        st = Table(subj_rows, colWidths=col_w)
        style_cmds = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dbeafe')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('ALIGN', (1, 0), (2, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]
        st.setStyle(TableStyle(style_cmds))
        elements.append(st)
        elements.append(Spacer(1, 6))

        # ======== RUMUSAN (matching Excel Row 36-46) ========
        jum = student.get('jumlah_markah', '')
        purata = student.get('purata', '')
        gp = student.get('gp', '')
        analisis = student.get('analisis', '')
        keputusan = student.get('keputusan', '')
        kdk = student.get('kdk', '')
        kdt = student.get('kdt', '')
        kehadiran = student.get('kehadiran', '')
        ulasan = student.get('ulasan', '')

        jum_str = f"{float(jum):.2f}" if isinstance(jum, (int, float)) else str(jum or '')
        purata_str = f"{float(purata):.2f}" if isinstance(purata, (int, float)) else str(purata or '')
        gp_str = f"{float(gp):.2f}" if isinstance(gp, (int, float)) and gp < 90 else str(gp or '')

        rumusan_title = [[Paragraph('<b>RUMUSAN</b>', ParagraphStyle('RT', parent=styles['Normal'],
                          fontSize=9, fontName='Helvetica-Bold', alignment=1))]]
        rt = Table(rumusan_title, colWidths=[pw])
        rt.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#dbeafe')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(rt)

        rumusan_rows = [
            [Paragraph('JUMLAH MARKAH', rumusan_lbl), Paragraph(jum_str, rumusan_val)],
            [Paragraph('PURATA', rumusan_lbl), Paragraph(purata_str, rumusan_val)],
            [Paragraph('GRED PURATA', rumusan_lbl), Paragraph(gp_str, rumusan_val)],
            [Paragraph('ANALISIS', rumusan_lbl), Paragraph(str(analisis or ''), rumusan_val)],
            [Paragraph('KEPUTUSAN', rumusan_lbl), Paragraph(str(keputusan or ''), rumusan_val)],
            [Paragraph('KEDUDUKAN DALAM KELAS', rumusan_lbl), Paragraph(str(kdk or ''), rumusan_val)],
            [Paragraph('KEDUDUKAN DALAM TINGKATAN', rumusan_lbl), Paragraph(str(kdt or ''), rumusan_val)],
            [Paragraph('KEHADIRAN', rumusan_lbl), Paragraph(str(kehadiran or ''), rumusan_val)],
            [Paragraph('ULASAN GURU KELAS', rumusan_lbl), Paragraph(str(ulasan or ''), val_s)],
        ]
        rut = Table(rumusan_rows, colWidths=[6*cm, pw - 6*cm])
        rut.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(rut)
        elements.append(Spacer(1, 20))

        # ======== SIGNATURES (matching Excel Row 50-53) ========
        sig_data = [
            [Paragraph('........................................................', sig_dots),
             Paragraph('', sig_dots),
             Paragraph('........................................................', sig_dots)],
            [Paragraph(f'<b>{guru_kelas_name}</b>' if guru_kelas_name else '', sig_name_s),
             Paragraph('', sig_dots),
             Paragraph(f'<b>{principal}</b>', sig_name_s)],
            [Paragraph('Guru Kelas', sig_label_s),
             Paragraph('', sig_dots),
             Paragraph('Pengetua', sig_label_s)],
            [Paragraph(class_name, sig_label_s),
             Paragraph('', sig_dots),
             Paragraph(school_name, sig_label_s)],
        ]
        sgt = Table(sig_data, colWidths=[7*cm, pw - 14*cm, 7*cm])
        sgt.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
        ]))
        elements.append(sgt)

    doc.build(elements)
    buffer.seek(0)
    return buffer

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
