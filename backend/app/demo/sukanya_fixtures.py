"""
Sukanya Samriddhi Account Scheme, 2019 — Pre-verified Section Fixtures.

Contains exact section-by-section:
  1. Plain-Language English Simplification
  2. Full Hindi Translation (पूर्ण हिंदी अनुवाद)
  3. Plain-Language Hindi Simplification (सरल हिंदी)
  4. Preserved administrative conditions and entities for verified fidelity evaluation.
"""
from typing import Any

SUKANYA_SECTIONS: list[dict[str, Any]] = [
    {
        "id": "preamble",
        "title": "Background & Notification (Preamble)",
        "keywords": [
            "g.s.r. 914(e)",
            "g.s.r. 288(e)",
            "section 3a",
            "government savings promotion act",
            "powers conferred",
            "makes the following scheme",
        ],
        "simplified_english": (
            "The Central Government issued the Sukanya Samriddhi Account Scheme under the "
            "Government Savings Promotion Act, 1873. The scheme is called the Sukanya Samriddhi "
            "Account Scheme, 2019. It came into force on the date it was published in the Official Gazette. "
            "The document says that the scheme was notified through G.S.R. 914(E) dated 12 December 2019 "
            "and amended through G.S.R. 288(E) dated 5 May 2020."
        ),
        "translated_hindi": (
            "सुकन्या समृद्धि खाता योजना (G.S.R. 914(E) दिनांक 12/12/2019 द्वारा अधिसूचित तथा "
            "G.S.R. 288(E) दिनांक 05/05/2020 द्वारा संशोधित) — सरकारी बचत संवर्धन अधिनियम, 1873 (1873 का 5) "
            "की धारा 3A द्वारा प्रदत्त शक्तियों का प्रयोग करते हुए, केंद्र सरकार एतद्द्वारा यह योजना बनाती है।"
        ),
        "simplified_hindi": (
            "सुकन्या समृद्धि खाता योजना, 2019 केंद्र सरकार की एक बचत योजना है। इसे सरकारी बचत संवर्धन अधिनियम, "
            "1873 के तहत बनाया गया है। यह योजना 12 दिसंबर 2019 को G.S.R. 914(E) के जरिए अधिसूचित की गई और "
            "5 मई 2020 को G.S.R. 288(E) द्वारा संशोधित की गई। यह राजपत्र में छपने की तारीख से लागू हुई।"
        ),
        "preserved_conditions": [
            "Government Savings Promotion Act, 1873",
            "Section 3A statutory authority",
            "G.S.R. 914(E) dated 12/12/2019",
            "G.S.R. 288(E) dated 05/05/2020",
        ],
        "preserved_entities": ["914(E)", "12/12/2019", "288(E)", "05/05/2020", "3A", "1873"],
    },
    {
        "id": "section_1",
        "title": "1. Short Title and Commencement",
        "keywords": [
            "short title",
            "commencement",
            "called the sukanya samriddhi",
            "official gazette",
        ],
        "simplified_english": (
            "1. The scheme is named the Sukanya Samriddhi Account Scheme, 2019.\n"
            "2. It became effective on the date it was published in the Official Gazette."
        ),
        "translated_hindi": (
            "1. संक्षिप्त नाम और प्रारंभ: (1) इस योजना को सुकन्या समृद्धि खाता योजना, 2019 कहा जा सकता है।\n"
            "(2) यह योजना राजपत्र (Official Gazette) में प्रकाशित होने की तारीख से लागू होगी।"
        ),
        "simplified_hindi": (
            "1. योजना का नाम और शुरुआत: इस योजना का नाम 'सुकन्या समृद्धि खाता योजना, 2019' है। "
            "यह सरकारी राजपत्र में छपने की तारीख से तुरंत लागू हो गई।"
        ),
        "preserved_conditions": [
            "Scheme name: Sukanya Samriddhi Account Scheme, 2019",
            "Commencement date: Date of publication in Official Gazette",
        ],
        "preserved_entities": ["2019"],
    },
    {
        "id": "section_2",
        "title": "2. Definitions",
        "keywords": [
            "definitions",
            "account holder means a girl child",
            "birth certificate means",
            "citizenship act",
            "financial year means",
            "twenty-one years from the date of its opening",
        ],
        "simplified_english": (
            "In this scheme:\n"
            "1. Account means an account opened under this scheme.\n"
            "2. Account holder means the girl child in whose name the account is opened.\n"
            "3. Act means the Government Savings Promotion Act, 1873.\n"
            "4. Birth certificate means a certificate issued by a municipal authority, an office authorised to register births and deaths, or an Indian Consulate.\n"
            "5. Family means a person, their spouse, and their children, including adopted children.\n"
            "6. Financial year means the period from 1 April to 31 March of the following year.\n"
            "7. Maturity means the account completing 21 years from the date it was opened."
        ),
        "translated_hindi": (
            "2. परिभाषाएँ: (1) इस योजना में: 'खाता' से अभिप्राय इस योजना के अंतर्गत खोले गए खाते से है; "
            "'खाताधारक' से अभिप्राय उस बालिका से है जिसके नाम पर खाता रखा गया है; "
            "'अधिनियम' से अभिप्राय सरकारी बचत संवर्धन अधिनियम, 1873 (1873 का 5) से है; "
            "'परिवार' में व्यक्ति, उसका पति/पत्नी तथा बच्चे (गोद लिए बच्चे सहित) शामिल हैं; "
            "'वित्तीय वर्ष' 1 अप्रैल से 31 मार्च की अवधि है; "
            "'परिपक्वता' से अभिप्राय खाता खोलने की तारीख से इक्कीस वर्ष की अवधि पूरी होने से है।"
        ),
        "simplified_hindi": (
            "2. जरूरी शब्दों का मतलब:\n"
            "- खाता: इस योजना के तहत खोला गया खाता।\n"
            "- खाताधारक: वह लड़की जिसके नाम पर खाता है।\n"
            "- परिवार: माता-पिता और उनके बच्चे (गोद लिए बच्चे भी शामिल)।\n"
            "- वित्तीय वर्ष: 1 अप्रैल से अगले साल 31 मार्च तक।\n"
            "- परिपक्वता: खाता खुलने के पूरे 21 साल होना।"
        ),
        "preserved_conditions": [
            "Account holder defined as girl child",
            "Financial year defined as 1 April to 31 March",
            "Maturity defined as 21 years from opening date",
            "Family definition includes adopted children",
        ],
        "preserved_entities": ["1873", "1955", "2018", "21"],
    },
    {
        "id": "section_3",
        "title": "3. Opening of Account",
        "keywords": [
            "opening of account",
            "age of ten years",
            "single account under this scheme",
            "form-1",
            "maximum of two girl children",
            "twins/triplets",
            "second order of birth",
        ],
        "simplified_english": (
            "1. A guardian can open an account in the name of a girl child who is below 10 years old on the opening date.\n"
            "2. Each girl child can have only one account under this scheme.\n"
            "3. The guardian must submit Form 1, the girl's birth certificate, and the guardian's required documents.\n"
            "4. Normally, a family can open accounts for a maximum of two girl children.\n"
            "Exception: More than two accounts may be opened if additional girl children are twins or triplets born in the first or second birth order, supported by an affidavit and birth certificates. This exception does not apply if the first birth order already resulted in two or more surviving girls."
        ),
        "translated_hindi": (
            "3. खाता खोलना: (1) कोई अभिभावक ऐसी बालिका के नाम पर खाता खोल सकता है जिसने खाता खोलने की तारीख तक दस वर्ष की आयु पूरी न की हो। "
            "(2) प्रत्येक खाताधारक का केवल एक ही खाता होगा। (3) आवेदन प्रपत्र-1 में जन्म प्रमाणपत्र और अभिभावक के दस्तावेज़ों के साथ जमा होगा। "
            "(4) एक परिवार में अधिकतम दो बालिकाओं के लिए खाते खोले जा सकते हैं। परंतु जुड़वाँ/तीन बच्चियों के जन्म की स्थिति में शपथपत्र और प्रमाणपत्र देने पर दो से अधिक खाते खोले जा सकते हैं।"
        ),
        "simplified_hindi": (
            "3. खाता कौन और कब खोल सकता है?\n"
            "1. अभिभावक उस लड़की के नाम पर खाता खोल सकते हैं जिसकी उम्र 10 साल से कम हो।\n"
            "2. एक लड़की का सिर्फ एक ही खाता खुल सकता है।\n"
            "3. खाता खोलने के लिए Form 1, जन्म प्रमाणपत्र और अभिभावक के पहचान पत्र जरूरी हैं।\n"
            "4. एक परिवार में सामान्यतः अधिकतम दो लड़कियों के खाते खुल सकते हैं।\n"
            "विशेष छूट: जुड़वाँ या तीन बच्चियों के जन्म पर शपथपत्र देकर दो से ज्यादा खाते भी खोले जा सकते हैं।"
        ),
        "preserved_conditions": [
            "Age limit: below 10 years on opening date",
            "Single account per girl child restriction",
            "Mandatory submission of Form 1 and birth certificate",
            "Maximum two girl children per family limit",
            "Twins/triplets exception with affidavit proof",
        ],
        "preserved_entities": ["10", "1", "2"],
    },
    {
        "id": "section_4",
        "title": "4. Deposits",
        "keywords": [
            "deposits",
            "minimum initial deposit of two hundred and fifty",
            "multiples of fifty rupees",
            "one lakh fifty thousand rupees",
            "period of fifteen years",
            "account under default",
            "penalty of fifty rupees",
        ],
        "simplified_english": (
            "1. The account can be opened with at least ₹250. Subsequent deposits must be in multiples of ₹50.\n"
            "2. At least ₹250 must be deposited in each financial year.\n"
            "3. Total deposits cannot exceed ₹1,50,000 in a financial year. Any excess amount deposited by accounting error earns no interest and must be refunded immediately.\n"
            "4. Deposits can be made for 15 years from the account-opening date.\n"
            "Default rule: If minimum ₹250 is missed, a penalty of ₹50 per year of default plus the minimum deposit regularises the account within 15 years. Otherwise, the balance continues earning scheme interest until closure."
        ),
        "translated_hindi": (
            "4. जमा राशि: (1) खाता कम-से-कम ₹250 की प्रारंभिक राशि से खोला जा सकता है और इसके बाद जमा ₹50 के गुणकों में होगी। "
            "प्रत्येक वित्तीय वर्ष में न्यूनतम ₹250 जमा करना अनिवार्य है। (2) एक वित्तीय वर्ष में कुल जमा ₹1,50,000 से अधिक नहीं होगी। "
            "गलती से ली गई अधिक राशि पर ब्याज नहीं मिलेगा और वह तुरंत वापस की जाएगी। (3) खाता खोलने से 15 वर्ष तक जमा किया जा सकता है। "
            "(4) न्यूनतम राशि जमा न करने पर खाता डिफॉल्ट होगा, जिसे ₹50 प्रति वर्ष जुर्माना देकर 15 वर्ष के भीतर नियमित किया जा सकता है।"
        ),
        "simplified_hindi": (
            "4. खाते में कितना पैसा जमा करना होगा?\n"
            "- खाता कम-से-कम ₹250 से खुलता है और बाद में ₹50 के गुणकों में जमा किया जा सकता है।\n"
            "- हर साल कम-से-कम ₹250 जमा करना जरूरी है।\n"
            "- एक साल में अधिकतम ₹1,50,000 ही जमा किए जा सकते हैं।\n"
            "- खाता खुलने के 15 साल तक पैसे जमा किए जा सकते हैं।\n"
            "- यदि किसी साल ₹250 जमा न हों, तो हर साल के लिए ₹50 जुर्माना देकर 15 साल में खाता नियमित कराया जा सकता है।"
        ),
        "preserved_conditions": [
            "Minimum initial deposit: Rs 250",
            "Deposit increments: multiples of Rs 50",
            "Minimum annual deposit: Rs 250 per financial year",
            "Maximum annual ceiling: Rs 1,50,000 per financial year",
            "Deposit tenure: 15 years from opening date",
            "Default penalty: Rs 50 for each default year",
        ],
        "preserved_entities": ["250", "50", "1,50,000", "15"],
    },
    {
        "id": "section_5",
        "title": "5. Interest on Deposit",
        "keywords": [
            "interest on deposit",
            "12th december, 2019 to 31st march, 2020",
            "8.4 per cent",
            "1st day of april, 2020",
            "7.6 per cent",
            "lowest balance in the account between the close of the fifth day",
            "fraction of a rupee",
        ],
        "simplified_english": (
            "The document provides these interest rates:\n"
            "- Deposits from 12 December 2019 through 31 March 2020 earn 8.4% per year.\n"
            "- Deposits made on or after 1 April 2020 earn 7.6% per year.\n\n"
            "Interest calculation rules:\n"
            "1. Calculated monthly on the lowest balance between the close of the 5th day and the end of the month.\n"
            "2. Interest is credited at the end of each financial year.\n"
            "3. Fractions of a rupee are rounded to the nearest rupee (50 paise or more rounds up to ₹1; under 50 paise is ignored)."
        ),
        "translated_hindi": (
            "5. जमा राशि पर ब्याज: (1) 12 दिसंबर 2019 से 31 मार्च 2020 तक खाते में जमा और शेष राशि पर 8.4% वार्षिक ब्याज मिलेगा। "
            "(1A) 1 अप्रैल 2020 को या उसके बाद जमा और शेष राशि पर 7.6% वार्षिक ब्याज मिलेगा। "
            "(2) ब्याज की गणना महीने की 5वीं तारीख की समाप्ति से माह के अंत तक के न्यूनतम शेष पर की जाएगी तथा प्रत्येक वित्तीय वर्ष के अंत में जमा होगी। "
            "50 पैसे या अधिक को ₹1 माना जाएगा तथा 50 पैसे से कम को छोड़ दिया जाएगा।"
        ),
        "simplified_hindi": (
            "5. ब्याज कैसे मिलता है?\n"
            "- 12 दिसंबर 2019 से 31 मार्च 2020 तक: 8.4% सालाना ब्याज।\n"
            "- 1 अप्रैल 2020 से आगे: 7.6% सालाना ब्याज।\n"
            "- हर महीने की 5 तारीख के बाद से महीने के आखिरी दिन तक रहे न्यूनतम बैलेंस पर ब्याज निकाला जाता है।\n"
            "- ब्याज हर साल 31 मार्च (वित्तीय वर्ष के अंत) को खाते में जुड़ जाता है।"
        ),
        "preserved_conditions": [
            "8.4% per annum interest rate (12 Dec 2019 to 31 Mar 2020)",
            "7.6% per annum interest rate (from 1 April 2020 onwards)",
            "Monthly calculation based on lowest balance between 5th and month-end",
            "Interest credited annually at end of financial year",
            "Rounding rule: 50 paise or more rounded up to Rs 1",
        ],
        "preserved_entities": ["12", "2019", "31", "2020", "8.4", "1", "7.6", "5"],
    },
    {
        "id": "section_6",
        "title": "6. Operation of Account",
        "keywords": [
            "operation of account",
            "operated by the guardian till the account holder attains the age of eighteen",
            "operated by the account holder herself",
        ],
        "simplified_english": (
            "1. The guardian operates the account until the girl reaches 18 years of age.\n"
            "2. After turning 18, the girl child herself operates the account after submitting the necessary documents."
        ),
        "translated_hindi": (
            "6. खाते का संचालन: (1) खाताधारक के अठारह वर्ष की आयु पूरी करने तक खाते का संचालन अभिभावक करेगा। "
            "अठारह वर्ष की आयु पूरी करने के बाद खाताधारक स्वयं आवश्यक दस्तावेज़ जमा करके खाते का संचालन करेगी।"
        ),
        "simplified_hindi": (
            "6. खाते को कौन चला सकता है?\n"
            "- लड़की के 18 साल की होने तक उसका अभिभावक खाता चलाएगा।\n"
            "- 18 साल की होने के बाद लड़की जरूरी कागजात जमा करके खुद अपना खाता चला सकती है।"
        ),
        "preserved_conditions": [
            "Guardian operates account until girl child turns 18",
            "Girl child operates account herself upon turning 18",
        ],
        "preserved_entities": ["18"],
    },
    {
        "id": "section_7",
        "title": "7. Premature Closure of Account",
        "keywords": [
            "premature closure",
            "death of the account holder",
            "form-2",
            "post office savings account",
            "extreme compassionate grounds",
            "life-threatening diseases",
            "death of the guardian",
            "before completion of five years",
        ],
        "simplified_english": (
            "A. On Death of Account Holder:\n"
            "The account is closed immediately upon Form 2 application and death certificate. The balance and accrued interest are paid to the guardian. Interest between death and closure is paid at Post Office Savings Account rate.\n\n"
            "B. On Extreme Compassionate / Hardship Grounds:\n"
            "Early closure may be allowed for life-threatening medical treatment of the girl or death of the guardian causing undue hardship, backed by complete documentation and a written order.\n"
            "Restriction: No premature closure under hardship is permitted before completing 5 years from account opening."
        ),
        "translated_hindi": (
            "7. समय से पहले खाता बंद करना: (1) खाताधारक की मृत्यु की स्थिति में मृत्यु प्रमाणपत्र और प्रपत्र-2 में आवेदन पर खाता तुरंत बंद होगा और राशि अभिभावक को दी जाएगी। "
            "(2) मृत्यु और बंद होने के बीच डाकघर बचत खाता दर से ब्याज मिलेगा। "
            "(3) जानलेवा बीमारी या अभिभावक की मृत्यु जैसी अत्यंत मानवीय परिस्थितियों में उचित कठिनाई सिद्ध होने पर लिखित आदेश द्वारा खाता बंद हो सकता है। "
            "परंतु खाता खोलने से 5 वर्ष पूरे होने से पहले समयपूर्व बंद करने की अनुमति नहीं होगी।"
        ),
        "simplified_hindi": (
            "7. समय से पहले खाता कब बंद हो सकता है?\n"
            "A. लड़की की मृत्यु होने पर: Form 2 और मृत्यु प्रमाणपत्र देकर खाता बंद होगा और पूरी रकम अभिभावक को मिलेगी।\n"
            "B. गंभीर बीमारी या अभिभावक की मृत्यु पर: इलाज या बहुत भारी परेशानी के समय लिखित आदेश से खाता बंद हो सकता है।\n"
            "शर्त: खाता खुलने के कम-से-कम 5 साल पूरे होने के बाद ही यह छूट मिल सकती है।"
        ),
        "preserved_conditions": [
            "Immediate closure on death of account holder with Form 2",
            "Post Office Savings Account interest rate applied post-death",
            "Hardship closure permitted for life-threatening illness or guardian death",
            "Mandatory 5-year lock-in restriction before hardship closure permitted",
        ],
        "preserved_entities": ["2", "5"],
    },
    {
        "id": "section_8",
        "title": "8. Withdrawal for Education",
        "keywords": [
            "withdrawal",
            "form-3",
            "maximum of fifty per cent",
            "purpose of education",
            "attains the age of eighteen years or has passed tenth standard",
            "confirmed offer of admission",
            "fee-slip",
            "maximum of five years",
        ],
        "simplified_english": (
            "1. Money can be withdrawn for higher education by submitting Form 3.\n"
            "2. Maximum withdrawal is 50% of the balance at the end of the preceding financial year.\n"
            "3. Allowed once the girl turns 18 years old or passes Class 10 (whichever is earlier).\n"
            "4. Must be supported by a confirmed admission offer or institutional fee slip.\n"
            "5. May be withdrawn in a lump sum or in yearly instalments (max 1 withdrawal per year, up to 5 years), capped at actual admission fees and charges."
        ),
        "translated_hindi": (
            "8. निकासी: (1) प्रपत्र-3 में आवेदन पर खाताधारक की शिक्षा के लिए पिछले वित्तीय वर्ष के अंत में उपलब्ध शेष का अधिकतम 50% निकाला जा सकता है। "
            "यह अनुमति खाताधारक के 18 वर्ष पूरे करने या 10वीं कक्षा पास करने पर (जो भी पहले हो) मिलेगी। "
            "(2) प्रवेश का पक्का प्रस्ताव या फीस-पर्ची संलग्न करना अनिवार्य है। "
            "(3) निकासी एकमुश्त या अधिकतम 5 वर्षों तक प्रति वर्ष एक किस्त में की जा सकती है, जो वास्तविक प्रवेश शुल्क तक ही सीमित होगी।"
        ),
        "simplified_hindi": (
            "8. पढ़ाई के लिए पैसे निकालना:\n"
            "- उच्च शिक्षा के लिए Form 3 भरकर खाते से पैसे निकाले जा सकते हैं।\n"
            "- पिछले साल के अंत में जमा कुल बैलेंस का अधिकतम 50% निकाला जा सकता है।\n"
            "- यह सुविधा लड़की के 18 साल की होने पर या 10वीं कक्षा पास करने पर (जो भी पहले हो) मिलती है।\n"
            "- कॉलेज/संस्थान का प्रवेश पत्र या फीस की रसीद दिखाना जरूरी है।\n"
            "- पैसे एक बार में या 5 साल तक सालाना किस्तों में निकाले जा सकते हैं।"
        ),
        "preserved_conditions": [
            "Maximum withdrawal limit: 50% of preceding financial year-end balance",
            "Purpose restricted to education of account holder",
            "Eligibility threshold: attains 18 years or passes 10th standard",
            "Documentary proof required: confirmed admission offer or fee-slip",
            "Instalment option: max 1 withdrawal per year for up to 5 years",
        ],
        "preserved_entities": ["3", "50", "18", "10", "5"],
    },
    {
        "id": "section_9",
        "title": "9. Closure on Maturity",
        "keywords": [
            "closure on maturity",
            "mature on completion of a period of twenty-one years",
            "intended marriage",
            "non-judicial stamp paper attested by the notary",
            "not be less than eighteen years of age on the date of marriage",
            "one month from the date of the intended marriage or after three months",
            "form-4",
        ],
        "simplified_english": (
            "1. The account matures 21 years after the opening date.\n"
            "2. Early closure is permitted for the girl's marriage if she will be at least 18 years old on the marriage date.\n"
            "3. Marriage early closure requires an application, notarised declaration on non-judicial stamp paper, and proof of age.\n"
            "4. Window restriction: Cannot be closed earlier than 1 month before or later than 3 months after the marriage date.\n"
            "5. Account balance and interest are paid upon application in Form 4."
        ),
        "translated_hindi": (
            "9. परिपक्वता पर खाता बंद करना: (1) खाता खोलने से 21 वर्ष की अवधि पूरी होने पर खाता परिपक्व होगा। "
            "(2) शादी के आधार पर समयपूर्व बंद करने के लिए नोटरी द्वारा प्रमाणित शपथपत्र और 18 वर्ष आयु का प्रमाण देना होगा। "
            "यह अनुमति शादी की तारीख से 1 महीने पहले से 3 महीने बाद तक ही वैध होगी। "
            "(3) प्रपत्र-4 में आवेदन करने पर मूलधन और लागू ब्याज खाताधारक को दे दिया जाएगा।"
        ),
        "simplified_hindi": (
            "9. खाता कब पूरा होगा?\n"
            "- खाता खुलने के 21 साल बाद परिपक्व (Mature) होता है।\n"
            "- लड़की की शादी होने पर 21 साल से पहले भी खाता बंद किया जा सकता है (शादी के दिन उम्र कम-से-कम 18 साल होनी चाहिए)।\n"
            "- इसके लिए नोटरी से प्रमाणित शपथपत्र देना होता है।\n"
            "- शादी से 1 महीने पहले से लेकर शादी के 3 महीने बाद तक ही खाता बंद कराया जा सकता है।\n"
            "- Form 4 भरकर पूरी रकम और ब्याज निकाला जा सकता है।"
        ),
        "preserved_conditions": [
            "Maturity tenure: 21 years from account opening",
            "Marriage early closure permitted if age >= 18 on marriage date",
            "Submission of notarised declaration on non-judicial stamp paper",
            "Timing window: between 1 month prior and 3 months after marriage",
            "Final payout claimed via Form 4",
        ],
        "preserved_entities": ["21", "18", "1", "3", "4"],
    },
    {
        "id": "section_10_11",
        "title": "10 & 11. General Rules and Power to Relax",
        "keywords": [
            "application of general rules",
            "general rules, 2018",
            "power to relax",
            "central government is satisfied",
            "causes undue hardship",
            "recorded in writing",
        ],
        "simplified_english": (
            "10. The Government Savings Promotion General Rules, 2018 apply to any matter not specifically covered by this scheme.\n"
            "11. The Central Government has the power to relax any provision of this scheme if it causes undue hardship to an account holder, provided reasons are recorded in writing and the relaxation does not violate the parent Act."
        ),
        "translated_hindi": (
            "10. सामान्य नियमों का लागू होना: जिन मामलों का इसमें प्रावधान नहीं है, उनमें सामान्य नियम, 2018 प्रभावी होंगे।\n"
            "11. नियमों में छूट देने की शक्ति: केंद्र सरकार अनुचित कठिनाई की स्थिति में लिखित कारणों के साथ किसी नियम में छूट दे सकती है, जो अधिनियम के विपरीत न हो।"
        ),
        "simplified_hindi": (
            "10. अन्य नियम: जिन बातों का उल्लेख इस योजना में नहीं है, उन पर सरकारी सामान्य नियम 2018 लागू होंगे।\n"
            "11. सरकार द्वारा छूट: यदि किसी नियम से खाताधारक को भारी परेशानी हो रही हो, तो केंद्र सरकार लिखित कारण देकर उस नियम में छूट दे सकती है।"
        ),
        "preserved_conditions": [
            "Application of Government Savings Promotion General Rules, 2018",
            "Central Government power to relax provisions for undue hardship",
            "Mandatory recording of reasons in writing for any exemption",
        ],
        "preserved_entities": ["2018"],
    },
]


def match_sukanya_section(chunk_text: str) -> dict[str, Any] | None:
    """
    Identifies which of the 11 Sukanya Samriddhi sections a chunk corresponds to.
    Uses paragraph scoring based on key phrases and numerical markers.
    """
    if not chunk_text or not chunk_text.strip():
        return None

    text_lower = chunk_text.lower()

    # Guard: check if this is the Sukanya Samriddhi document
    is_sukanya = (
        "sukanya" in text_lower
        or "g.s.r. 914(e)" in text_lower
        or "g.s.r. 288(e)" in text_lower
        or "girl child" in text_lower
        or "savings promotion act" in text_lower
    )
    if not is_sukanya:
        return None

    best_match: dict[str, Any] | None = None
    best_score = 0

    for section in SUKANYA_SECTIONS:
        score = 0
        for kw in section["keywords"]:
            if kw in text_lower:
                # Longer keywords give higher match confidence
                score += len(kw.split())

        if score > best_score:
            best_score = score
            best_match = section

    # Return best matching section if confidence threshold met
    if best_score >= 1:
        return best_match

    # Default to preamble/first section if general Sukanya text
    return SUKANYA_SECTIONS[0]
