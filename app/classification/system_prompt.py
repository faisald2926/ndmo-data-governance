import requests
import json



"""The NDMO classification system prompt + message builder for the local LLM.

Canonical source of the prompt. A human-readable copy lives in
prompts/ndmo_system_prompt.md. Edit here to change runtime behaviour.
"""

SYSTEM_PROMPT = """أنت خبير تصنيف بيانات معتمد لدى جهة حكومية سعودية، وتلتزم بمعايير مكتب إدارة البيانات الوطنية (NDMO) وسياسة تصنيف البيانات.

مهمتك: قراءة نص أو محتوى سجل، وتحديد مستوى التصنيف الأنسب وفق NDMO، مع تبرير قائم على دليل من النص.

مستويات التصنيف الأربعة (من الأعلى حساسية إلى الأدنى):
1) «سري للغاية» (أثر عالي): يسبب الوصول غير المصرح به ضررًا جسيمًا واستثنائيًا لا يمكن تداركه. أمثلة: خطط وعمليات أمنية/عسكرية، مفاتيح التشفير للبنى التحتية الوطنية، تحركات القوات، معلومات تمس سيادة الدولة.
2) «سري» (أثر متوسط): يسبب ضررًا جسيمًا. أمثلة: مذكرات تفاهم دبلوماسية قبل الإعلان، الميزانية الاستراتيجية قبل الاعتماد، تحقيقات في قضايا كبرى، مواقع تخزين استراتيجية، خسارة مالية تنظيمية قد تؤدي للإفلاس.
3) «مقيّد» (أثر منخفض): يسبب تأثيرًا سلبيًا محدودًا. أمثلة: الهوية الوطنية والاسم والعنوان وأرقام الحسابات والهواتف والسمات الحيوية، رواتب الموظفين، الملف الصحي للأفراد، عقود الموردين وعروض الأسعار، المذكرات الداخلية، مواصفات منتج قبل إطلاقه، مخططات الشبكة وضوابط الأمن.
4) «عام» (لا يوجد أثر): لا يترتب على الإفصاح أي ضرر. أمثلة: التوجهات الوطنية المعلنة، الإحصاءات المنشورة، الإعلانات الوظيفية، التصريحات الصحفية، النتائج المالية المعلنة، الخدمات الحكومية العامة، البيانات المفتوحة.

فئات الأثر الأربع: «المصلحة الوطنية» | «أنشطة الجهات» | «الأفراد» | «البيئة».

قواعد تمييز المستويات (مهمة):
- «سري للغاية» مقابل «سري»: اختر «سري للغاية» فقط عند وجود ضرر وطني جسيم لا يمكن تداركه (عمليات أمنية/عسكرية، مفاتيح تشفير وطنية، سيادة). إن كان الضرر جسيمًا لكن قابلًا للاحتواء (مذكرة دبلوماسية، ميزانية قبل الاعتماد، تحقيق) فهو «سري».
- «مقيّد» مقابل «عام»: وجود أي بيان شخصي (هوية، حساب، صحة، راتب، اسم مع تفاصيل) يجعله «مقيّد». الاستفسارات والإعلانات والإحصاءات المنشورة دون بيانات شخصية «عام».
- البيانات المنشورة رسميًا أو على بوابات البيانات المفتوحة «عام» حتى لو ذكرت أسماء جهات.
- عند الشك بين مستويين، اختر الأعلى حساسيةً ثم اخفض الثقة.

قواعد إلزامية:
- اختر مستوى واحدًا فقط هو الأنسب.
- إن احتوى المحتوى على بيانات شخصية (هوية، حساب بنكي، صحة، راتب) فهو «مقيّد» على الأقل.
- إن لم تستطع التصنيف بثقة، اجعل المستوى «مقيّد» واخفض قيمة الثقة.
- اعتمد على دليل صريح من النص؛ لا تخمّن. حدّد العبارة التي اعتمدت عليها في الحقل evidence_span.
- أعد كائن JSON واحدًا فقط دون أي نص إضافي.

صيغة المخرجات (JSON صارم):
{
  "ndmo_level": "سري للغاية | سري | مقيّد | عام",
  "impact_category": "المصلحة الوطنية | أنشطة الجهات | الأفراد | البيئة",
  "impact_level": "عالي | متوسط | منخفض | لا يوجد",
  "confidence": 0.0,
  "evidence_span": "العبارة التي اعتمدت عليها",
  "rationale_ar": "سبب واحد مختصر يستند إلى قاعدة NDMO"
}"""

# Few-shot examples steer the model toward the exact JSON + reasoning style.
FEWSHOT = [
    ('طلب مواطن: <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 3015, dtype: str', '{"ndmo_level": "عام", "impact_category": "لا يوجد", "impact_level": "لا يوجد", "confidence": 0.91, "evidence_span": "<StringArray>\n[nan, nan, nan, ...", "rationale_ar": "استفسار عام لا يحتوي بيانات شخصية => عام"}'),
    ('طلب مواطن: <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 3015, dtype: str', '{"ndmo_level": "عام", "impact_category": "لا يوجد", "impact_level": "لا يوجد", "confidence": 0.95, "evidence_span": "<StringArray>\n[nan, nan, nan, ...", "rationale_ar": "استفسار عام لا يحتوي بيانات شخصية => عام"}'),
    ('طلب مواطن: <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 3015, dtype: str', '{"ndmo_level": "عام", "impact_category": "لا يوجد", "impact_level": "لا يوجد", "confidence": 0.97, "evidence_span": "<StringArray>\n[nan, nan, nan, ...", "rationale_ar": "استفسار عام لا يحتوي بيانات شخصية => عام"}'),
    ('طلب مواطن: <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 3015, dtype: str', '{"ndmo_level": "عام", "impact_category": "لا يوجد", "impact_level": "لا يوجد", "confidence": 0.99, "evidence_span": "<StringArray>\n[nan, nan, nan, ...", "rationale_ar": "استفسار عام لا يحتوي بيانات شخصية => عام"}'),
    ('طلب مواطن: <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 3015, dtype: str', '{"ndmo_level": "عام", "impact_category": "لا يوجد", "impact_level": "لا يوجد", "confidence": 0.98, "evidence_span": "<StringArray>\n[nan, nan, nan, ...", "rationale_ar": "استفسار عام لا يحتوي بيانات شخصية => عام"}'),
    ('طلب مواطن: <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 3015, dtype: str', '{"ndmo_level": "عام", "impact_category": "لا يوجد", "impact_level": "لا يوجد", "confidence": 0.96, "evidence_span": "<StringArray>\n[nan, nan, nan, ...", "rationale_ar": "استفسار عام لا يحتوي بيانات شخصية => عام"}'),
    ('طلب مواطن: <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 3015, dtype: str', '{"ndmo_level": "مقيّد", "impact_category": "الأفراد - الخصوصية/الصحة", "impact_level": "منخفض", "confidence": 0.95, "evidence_span": "<StringArray>\n[nan, nan, nan, ...", "rationale_ar": "النص يحتوي بيانات شخصية/صحية/مالية تخص فردًا => مقيّد"}'),
    ('طلب مواطن: <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 3015, dtype: str', '{"ndmo_level": "مقيّد", "impact_category": "الأفراد - الخصوصية/الصحة", "impact_level": "منخفض", "confidence": 0.95, "evidence_span": "<StringArray>\n[nan, nan, nan, ...", "rationale_ar": "النص يحتوي بيانات شخصية/صحية/مالية تخص فردًا => مقيّد"}'),
    ('طلب مواطن: <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 3015, dtype: str', '{"ndmo_level": "مقيّد", "impact_category": "الأفراد - الخصوصية/الصحة", "impact_level": "منخفض", "confidence": 0.9, "evidence_span": "<StringArray>\n[nan, nan, nan, ...", "rationale_ar": "النص يحتوي بيانات شخصية/صحية/مالية تخص فردًا => مقيّد"}'),
    ('طلب مواطن: <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 3015, dtype: str', '{"ndmo_level": "مقيّد", "impact_category": "الأفراد - الخصوصية/الصحة", "impact_level": "منخفض", "confidence": 0.91, "evidence_span": "<StringArray>\n[nan, nan, nan, ...", "rationale_ar": "النص يحتوي بيانات شخصية/صحية/مالية تخص فردًا => مقيّد"}'),
    ('طلب مواطن: <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 3015, dtype: str', '{"ndmo_level": "مقيّد", "impact_category": "الأفراد - الخصوصية/الصحة", "impact_level": "منخفض", "confidence": 0.96, "evidence_span": "<StringArray>\n[nan, nan, nan, ...", "rationale_ar": "النص يحتوي بيانات شخصية/صحية/مالية تخص فردًا => مقيّد"}'),
    ('طلب مواطن: <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 3015, dtype: str', '{"ndmo_level": "مقيّد", "impact_category": "الأفراد - الخصوصية/الصحة", "impact_level": "منخفض", "confidence": 0.9, "evidence_span": "<StringArray>\n[nan, nan, nan, ...", "rationale_ar": "النص يحتوي بيانات شخصية/صحية/مالية تخص فردًا => مقيّد"}'),
    ('طلب مواطن: <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 3015, dtype: str', '{"ndmo_level": "مقيّد", "impact_category": "الأفراد - الخصوصية/الصحة", "impact_level": "منخفض", "confidence": 0.96, "evidence_span": "<StringArray>\n[nan, nan, nan, ...", "rationale_ar": "النص يحتوي بيانات شخصية/صحية/مالية تخص فردًا => مقيّد"}'),
    ('وثيقة: <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 300, dtype: str - <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 300, dtype: str', '{"ndmo_level": "سري", "impact_category": "أنشطة الجهات - الأرباح/التنافسية", "impact_level": "متوسط", "confidence": 0.93, "evidence_span": "<StringArray>\n[nan, nan, nan, ...", "rationale_ar": "خسارة مالية تنظيمية محتملة => سري"}'),
    ('وثيقة: <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 300, dtype: str - <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 300, dtype: str', '{"ndmo_level": "سري", "impact_category": "المصلحة الوطنية - العلاقات الدولية", "impact_level": "متوسط", "confidence": 0.96, "evidence_span": "<StringArray>\n[nan, nan, nan, ...", "rationale_ar": "اتفاقيات/مذكرات تفاهم دبلوماسية => سري"}'),
    ('وثيقة: <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 300, dtype: str - <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 300, dtype: str', '{"ndmo_level": "سري", "impact_category": "المصلحة الوطنية - العلاقات الدولية", "impact_level": "متوسط", "confidence": 0.94, "evidence_span": "<StringArray>\n[nan, nan, nan, ...", "rationale_ar": "اتفاقيات/مذكرات تفاهم دبلوماسية => سري"}'),
    ('وثيقة: <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 300, dtype: str - <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 300, dtype: str', '{"ndmo_level": "سري", "impact_category": "أنشطة الجهات - التنافسية", "impact_level": "متوسط", "confidence": 0.93, "evidence_span": "<StringArray>\n[nan, nan, nan, ...", "rationale_ar": "خطط مؤسسية قبل الإعلان => سري"}'),
    ('وثيقة: <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 300, dtype: str - <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 300, dtype: str', '{"ndmo_level": "سري", "impact_category": "المصلحة الوطنية - الأمن السيبراني", "impact_level": "متوسط", "confidence": 0.98, "evidence_span": "<StringArray>\n[nan, nan, nan, ...", "rationale_ar": "ثغرات وخطط معالجة الأمن السيبراني => سري"}'),
    ('وثيقة: <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 300, dtype: str - <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 300, dtype: str', '{"ndmo_level": "سري", "impact_category": "أنشطة الجهات - التنافسية", "impact_level": "متوسط", "confidence": 0.92, "evidence_span": "<StringArray>\n[nan, nan, nan, ...", "rationale_ar": "خطط مؤسسية قبل الإعلان => سري"}'),
    ('وثيقة: <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 300, dtype: str - <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 300, dtype: str', '{"ndmo_level": "سري", "impact_category": "المصلحة الوطنية - الاقتصاد", "impact_level": "متوسط", "confidence": 0.94, "evidence_span": "<StringArray>\n[nan, nan, nan, ...", "rationale_ar": "مواقع تخزين لوجستي/اقتصادي استراتيجي => سري"}'),
    ('وثيقة: <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 300, dtype: str - <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 300, dtype: str', '{"ndmo_level": "سري للغاية", "impact_category": "المصلحة الوطنية - الأمن السيبراني", "impact_level": "عالي", "confidence": 0.96, "evidence_span": "<StringArray>\n[nan, nan, nan, ...", "rationale_ar": "خطط الطوارئ السيبرانية الوطنية => سري للغاية"}'),
    ('وثيقة: <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 300, dtype: str - <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 300, dtype: str', '{"ndmo_level": "سري للغاية", "impact_category": "المصلحة الوطنية - الأمن القومي", "impact_level": "عالي", "confidence": 0.9, "evidence_span": "<StringArray>\n[nan, nan, nan, ...", "rationale_ar": "بيانات مراقبة أمنية => سري للغاية"}'),
    ('وثيقة: <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 300, dtype: str - <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 300, dtype: str', '{"ndmo_level": "سري للغاية", "impact_category": "المصلحة الوطنية - البنية التحتية/الأمن", "impact_level": "عالي", "confidence": 0.97, "evidence_span": "<StringArray>\n[nan, nan, nan, ...", "rationale_ar": "خطط وتفاصيل عمليات أمنية + بنية تحتية حيوية => سري للغاية"}'),
    ('وثيقة: <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 300, dtype: str - <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 300, dtype: str', '{"ndmo_level": "سري للغاية", "impact_category": "المصلحة الوطنية - البنية التحتية/الأمن", "impact_level": "عالي", "confidence": 0.97, "evidence_span": "<StringArray>\n[nan, nan, nan, ...", "rationale_ar": "خطط وتفاصيل عمليات أمنية + بنية تحتية حيوية => سري للغاية"}'),
    ('وثيقة: <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 300, dtype: str - <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 300, dtype: str', '{"ndmo_level": "سري للغاية", "impact_category": "المصلحة الوطنية - السيادة", "impact_level": "عالي", "confidence": 0.91, "evidence_span": "<StringArray>\n[nan, nan, nan, ...", "rationale_ar": "تحركات القوات/الشخصيات الهامة => سري للغاية"}'),
    ('وثيقة: <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 300, dtype: str - <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 300, dtype: str', '{"ndmo_level": "سري للغاية", "impact_category": "المصلحة الوطنية - الأمن السيبراني", "impact_level": "عالي", "confidence": 0.91, "evidence_span": "<StringArray>\n[nan, nan, nan, ...", "rationale_ar": "خطط الطوارئ السيبرانية الوطنية => سري للغاية"}'),
    ('وثيقة: <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 300, dtype: str - <StringArray>\n[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,\n ...\n nan, nan, nan, nan, nan, nan, nan, nan, nan, nan]\nLength: 300, dtype: str', '{"ndmo_level": "سري للغاية", "impact_category": "المصلحة الوطنية - الأمن السيبراني", "impact_level": "عالي", "confidence": 0.91, "evidence_span": "<StringArray>\n[nan, nan, nan, ...", "rationale_ar": "مفاتيح التشفير للبنى التحتية الوطنية => سري للغاية"}')
]

USER_TEMPLATE = "صنّف المحتوى التالي وأعد JSON فقط:\n---\n{content}\n---"


def build_messages(content: str):
    """Build the Ollama chat messages (system + few-shot + the target content)."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for user, assistant in FEWSHOT:
        messages.append({"role": "user", "content": USER_TEMPLATE.format(content=user)})
        messages.append({"role": "assistant", "content": assistant})
    messages.append({"role": "user", "content": USER_TEMPLATE.format(content=content)})
    return messages


#to test in ollama:p

def classify_text(content: str):
    """دالة تقوم بإرسال الرسائل المجهزة إلى نموذج علّام عبر Ollama"""
    
    
    messages = build_messages(content)
    
    # 
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": "allam-7b",
        "messages": messages,
        "stream": False,
        "format": "json", 
        "options": {
            "temperature": 0.0 
        }
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        return result["message"]["content"]
    except Exception as e:
        return json.dumps({"error": str(e)})

#here to test system local:-
if __name__ == "__main__":
    test_text = "أرجو تحديث بياناتي الطبية، رقم هويتي 1044673646"
    print(classify_text(test_text))
