# Flagged knowledge files: review and proposed corrections

**Status: approved; initial corrections and retrieval controls implemented. Content reconstruction remains in progress.** See [implementation results and remaining work](knowledge-review-implementation.md).

This report covers all **78 files** in the current metadata review queue: 62 have an unverified university label, 20 have an ambiguous topic, and four have both flags. They contain **414 extracted records from 16 local PDFs**. Each file has an individual recommendation below. The recommendations below record the original review. Subsequent implementation is tracked separately; the original source package remains preserved.

## What was reviewed

The review used the current loader's queue, the flagged files' record text and page references, source-PDF text, and selected rendered source pages. All 16 source PDFs are present locally, and all 414 record references point to valid page numbers. Longer files were reviewed through their record inventory and excerpts, with source sections checked for the proposed classification decisions. This is a file-level remediation review, not a line-by-line certification of every extracted fact or table cell.

Page numbers below mean **physical PDF pages**, counting the cover as page 1. They may differ from the page numbers printed inside the guide. `R1`, `R2`, and similar labels refer to the numbered records in the current TXT file.

The review establishes what these supplied documents say about their own identity and subject matter. It does not verify that each local PDF is the latest official publication, validate its download provenance, or independently confirm current tuition, immigration rules, rankings, or deadlines. Preserve those distinctions when approving content for students.

## Main findings and recommended order

1. **Resolve the four placeholder source groups.** The local source documents identify Yeungnam University College, Gachon University, and Kongju National University. This resolves the institution-identification question for 62 files, but it does not make their content automatically correct.
2. **Repair misplaced facts before simply renaming files.** Several files already have a recognized topic but contain another subject. The most serious examples are financial-support forms labeled as health insurance, scholarship percentages labeled as tuition, and an admissions timetable labeled as an interview assessment.
3. **Reconstruct whole source sections where tables were flattened.** Program availability, admission rounds, scholarships, fee tables, and department contacts need their original row and column relationships restored. Moving the existing broken text between files would preserve the error.
4. **Separate source metadata and navigation from answer evidence.** Covers, table-of-contents fragments, repeated footers, and bare form fields should be retained in the source archive or document metadata, but normally excluded as standalone answer passages.
5. **Check audience and source language.** KIT, Kunjang, and Woosuk material includes machine-translated general/domestic recruitment content. Domestic selection criteria must not become universal requirements for international applicants. Kunjang also includes material specifically about foreigners, so a blanket deletion of the whole source would discard useful content.
6. **Rebuild into a fresh collection after approval.** Renaming and splitting files changes chunk identities. The current indexer only upserts; it does not retire the old IDs automatically. Preserve the current collection until the replacement has passed checks.

## Source-level identity decisions

These decisions apply in addition to each file's individual correction.

| Current source group | Proposed canonical institution | Evidence in the local PDF | Recommendation |
|---|---|---|---|
| `Unverified_2027_1_en_pdf` — 14 files | `Yeungnam_University_College` | Cover, PDF p.1: English institution name and international special-admission title; p.8 gives the Global Admissions Team. | Replace the placeholder institution throughout the package. Preserve the college identity; do not merge it with a similarly named university. Use an undergraduate/college-program scope, with program-level duration retained. |
| `Unverified_2_eng2027_springsemesterfreshmantransferadmissionguideline_pdf` — 13 files | `Gachon_University` | PDF p.17 explicitly names Gachon University in the address and uses its institutional email/domain; p.1 identifies the 2027 spring undergraduate guide. | Set the institution to Gachon and degree scope to undergraduate. Preserve freshman versus transfer and English versus Korean track distinctions. |
| `Unverified_graduate_pdf` — 17 files | `Kongju_National_University` | `Graduate.pdf`, cover p.1, names Kongju National University and the 2027 spring graduate guide. | Replace the placeholder institution and retain graduate scope. Do not confuse Kongju with Kyungpook or Kyungbuk based on the abbreviation KNU. |
| `Unverified_undergraduate_pdf` — 18 files | `Kongju_National_University` | `Undergraduate.pdf`, cover p.1, names Kongju National University and the 2027 spring freshmen/transfer guide. | Use the same institution registry entry as the graduate guide, but preserve a separate source identity, degree scope, and admission rules. |

The current loader derives university labels from folder names. After approval, update folder paths, TXT headers, CSV entries, and corresponding JSONL records together. Do not edit only the displayed name in Qdrant.

## Proposed topic additions and domain assignments

Reuse existing topics wherever they fit. These additional topics would make the remaining material explicit; they have now been added to taxonomy version 2.

| Proposed topic | Domains | Use |
|---|---|---|
| `Admission_Policies` | `applications` | Cancellation, duplicate enrollment, applicant obligations, and interpretation precedence. Keep the applicable applicant route. |
| `Application_Forms` | `applications` | Instructions for completing or submitting a form. Blank fields alone are not answer evidence. |
| `Privacy_Consent` | `applications` | Source-specific application consent and data-use clauses. Do not turn them into general legal advice. |
| `Academic_Grading` | `education`, `applications` | GPA conversions and admissions scoring, with intact scales and applicability. |
| `University_Profile` | `universities` | Institutional background, clearly attributed to the source. Promotional claims need dates and attribution. |
| `University_Rankings` | `universities` | Ranking organization, year, category, position, and which institution or school is ranked. Incomplete claims stay out of retrieval. |
| `Campus_Location` | `universities`, `culture_life` | Verified address and campus/location descriptions. A map heading without the map has no usable location facts. |
| `Student_Support` | `culture_life` | Buddy programs, orientation, counseling, and other actual support services. |
| `Career_Support` | `education`, `universities` | Program career pathways and university career services. Do not classify these as permission to work under a student visa. |

Existing destinations include `Programs_Majors` (`education`, `universities`), `Eligibility_Academic` and `Eligibility_Language` (`education`, `applications`), `Financial_Proof` (`finances`, `applications`), `Tuition_Fees` and `Scholarships_Other` (`finances`), `Housing_Dormitory` (`accommodation`), `Health_Insurance` (`culture_life`, `finances`), `Contact_Information` (`universities`), and the existing application/document topics (`applications`). Keep tuition and living-cost amounts in separately labeled records, even when a passage has several domains.

## How to read the individual recommendations

Each item links to the current TXT file, names the source PDF, and lists its referenced pages. Its **proposed action** describes the correction; its **justification** identifies the evidence or failure being addressed. A recommendation to exclude means exclude from the active answer index while preserving the original material and the review history, not delete the source PDF.

For all source-group repairs, a classification decision can be high confidence even while the numerical details still require table reconstruction. No item is marked factually approved by this report.


### Source: HUFS_2027_Spring_Undergraduate_Admission_guide(ENG).pdf

Source PDF: [Open the local document](../data/pdfs/HUFS_2027_Spring_Undergraduate_Admission_guide%28ENG%29.pdf).


#### R001 - Other_Information.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Hankuk_University_of_Foreign_Studies/Undergraduate/HUFS_2027_Spring_Undergraduate_Admission_guide_ENG/Other_Information.txt).  
Current path: `Hankuk_University_of_Foreign_Studies/Undergraduate/HUFS_2027_Spring_Undergraduate_Admission_guide_ENG/Other_Information.txt`.  
Evidence: PDF pages 2; 1 extracted record(s). Flags: `unmapped_or_ambiguous_topic`.

**Proposed action:** Exclude this navigation fragment from answer retrieval. Keep the title as source metadata; recover usable contact links only if needed.

**Justification:** R1 on p.2 contains social-channel labels and a result-announcement heading, but no complete result date or substantive guidance.


### Source: 2027-Spring-Semester-Graduate-School-Admissions-Guide-HNU.pdf

Source PDF: [Open the local document](../data/pdfs/2027-Spring-Semester-Graduate-School-Admissions-Guide-HNU.pdf).


#### R002 - Other_Information.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Hannam_University/Graduate/2027_Spring_Semester_Graduate_School_Admissions_Guide_HNU/Other_Information.txt).  
Current path: `Hannam_University/Graduate/2027_Spring_Semester_Graduate_School_Admissions_Guide_HNU/Other_Information.txt`.  
Evidence: PDF pages 1, 13, 14; 3 extracted record(s). Flags: `unmapped_or_ambiguous_topic`.

**Proposed action:** Split R1 into Korean-language precedence metadata or Admission_Policies; move R2 to Documents_Verification; exclude R3 unless the actual campus map is extracted.

**Justification:** The three records are a language-precedence clause, academic-verification consent, and a bare campus-map heading, respectively. They do not share one factual topic.


#### R003 - Other_Policies.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Hannam_University/Graduate/2027_Spring_Semester_Graduate_School_Admissions_Guide_HNU/Other_Policies.txt).  
Current path: `Hannam_University/Graduate/2027_Spring_Semester_Graduate_School_Admissions_Guide_HNU/Other_Policies.txt`.  
Evidence: PDF pages 4, 5; 2 extracted record(s). Flags: `unmapped_or_ambiguous_topic`.

**Proposed action:** Reconstruct the pp.4-5 department table and merge into Programs_Majors, retaining Master's, Ph.D. and integrated-Ph.D. column headings and availability markers.

**Justification:** Both records are academic subjects and specializations, including Public Policy. Flattened circles and dashes have lost their degree-column relationships. This is not university-policy content.

**Implementation:** Reconstructed on 2026-10-27. Both program-table pages are active as reviewed replacements; the original flattened extraction remains held. See [R003 completion details](knowledge-review-implementation.md#hannam-graduate-programs-r003-completed).


### Source: Hannam University Bachelor_s.pdf

Source PDF: [Open the local document](../data/pdfs/Hannam%20University%20Bachelor_s.pdf).


#### R004 - Other_Information.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Hannam_University/Undergraduate/Hannam_University_Bachelor_s/Other_Information.txt).  
Current path: `Hannam_University/Undergraduate/Hannam_University_Bachelor_s/Other_Information.txt`.  
Evidence: PDF pages 4, 10, 11, 17, 20; 10 extracted record(s). Flags: `unmapped_or_ambiguous_topic`.

**Proposed action:** Split R1-R2 into Eligibility_Academic; rejoin R3-R4 with Apostille references under Documents_Verification; keep R5-R6 as a dated academic reference; attach R7 to its form instruction; reconstruct R8-R10 as Academic_Grading.

**Justification:** The file mixes overseas-schooling rules, country lists, a Korean-school list dated April 2025, a detached form instruction and a GPA conversion table. Preserve the table's grade scales and its source context.

**Implementation:** Reconstructed on 2026-10-27; corrected replacements are in the reviewed package and the original extraction remains held. See [undergraduate appendix results](knowledge-review-implementation.md#hannam-undergraduate-appendices-r004-and-r005-completed).


#### R005 - Other_Policies.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Hannam_University/Undergraduate/Hannam_University_Bachelor_s/Other_Policies.txt).  
Current path: `Hannam_University/Undergraduate/Hannam_University_Bachelor_s/Other_Policies.txt`.  
Evidence: PDF pages 16, 19; 2 extracted record(s). Flags: `unmapped_or_ambiguous_topic`.

**Proposed action:** Move both declarations to Admission_Policies or their associated Application_Forms. Rejoin R2 with its missing opening clause.

**Justification:** The pp.16 and 19 passages concern truthful application information and cancellation for false material. R2 starts mid-sentence; a generic policy label does not preserve the form context.

**Implementation:** Reconstructed on 2026-10-27; corrected replacements are in the reviewed package and the original extraction remains held. See [undergraduate appendix results](knowledge-review-implementation.md#hannam-undergraduate-appendices-r004-and-r005-completed).


### Source: KIT English Recruitment Guideline (1).pdf

Source PDF: [Open the local document](../data/pdfs/KIT%20English%20Recruitment%20Guideline%20%281%29.pdf).


#### R006 - Other_Information.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/KIT/Mixed/KIT_English_Recruitment_Guideline_1/Other_Information.txt).  
Current path: `KIT/Mixed/KIT_English_Recruitment_Guideline_1/Other_Information.txt`.  
Evidence: PDF pages 1, 2, 3, 5, 7, 9, 10, 11, 12, 13, 14, 15; 20 extracted record(s). Flags: `unmapped_or_ambiguous_topic`.

**Proposed action:** Hold domestic-route criteria out of international-applicant answers until applicability is established. Split pp.1-3 into attributed University_Profile/Career_Support; pp.5-9 into scoped programs, eligibility and documents; pp.10-12 into Academic_Grading; pp.13-15 into Admission_Policies. Resolve KIT's canonical name from the institutional logo before renaming.

**Justification:** The 20 records mix promotion, domestic high-school/GED/rural selection, scoring and registration restrictions. The source is explicitly machine-translated, and the translated title differs from the logo wording. Employment statistics do not establish permission to work on a student visa.


### Source: Korean Language Program.pdf

Source PDF: [Open the local document](../data/pdfs/Korean%20Language%20Program.pdf).


#### R007 - Other_Information.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Korean_Language_Program/Mixed/Korean_Language_Program/Other_Information.txt).  
Current path: `Korean_Language_Program/Mixed/Korean_Language_Program/Other_Information.txt`.  
Evidence: PDF pages 1; 1 extracted record(s). Flags: `unmapped_or_ambiguous_topic`.

**Proposed action:** Exclude this incomplete hospital-ranking fragment. If retained, reconstruct the complete attributed claim. Separately correct the source-package owner to Ajou University and label its non-degree Korean-language-course scope.

**Justification:** The record only contains a hospital-ranking phrase and an education-center label. The original p.1 brochure names Ajou University. Korean_Language_Program is a course label, not a university; the current prefix-based validator misses this identity issue.


### Source: Kunjang University College.pdf

Source PDF: [Open the local document](../data/pdfs/Kunjang%20University%20College.pdf).


#### R008 - Other_Information.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Kunjang_University_College/Mixed/Kunjang_University_College/Other_Information.txt).  
Current path: `Kunjang_University_College/Mixed/Kunjang_University_College/Other_Information.txt`.  
Evidence: PDF pages 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 26, 27, 28, 29, 30, 31, 33, 34, 35, 36, 38, 39; 58 extracted record(s). Flags: `unmapped_or_ambiguous_topic`.

**Proposed action:** Re-extract this 58-record file by source section and applicant route. Separate pp.3-10 admissions, quotas, eligibility and scoring; pp.15-36 programs, qualifications, career/student support and contacts. Exclude standalone headers/footers and reconstruct tables. Do not apply domestic criteria to foreigners without a source-specific basis.

**Justification:** R1 is a contents-like heading; R17, R29-R30 and R57-R58 are header noise. R14 explicitly includes an overseas Korean/foreigner route, so blanket exclusion of the whole PDF would lose relevant material. Later passages mix career destinations, curricula and staff contacts.


#### R009 - Other_Policies.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Kunjang_University_College/Mixed/Kunjang_University_College/Other_Policies.txt).  
Current path: `Kunjang_University_College/Mixed/Kunjang_University_College/Other_Policies.txt`.  
Evidence: PDF pages 23; 1 extracted record(s). Flags: `unmapped_or_ambiguous_topic`.

**Proposed action:** Reconstruct the p.23 physical-therapy curriculum/competency table and merge into Programs_Majors with course-to-competency relationships intact.

**Justification:** R1 lists clinical subjects, rehabilitation skills and field-practice competencies. Health and Medical Regulations is a curriculum item, not an institutional policy.


### Source: Tongmyong Master_s.pdf

Source PDF: [Open the local document](../data/pdfs/Tongmyong%20Master_s.pdf).


#### R010 - Other_Information.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Tongmyong_University/Graduate/Tongmyong_Master_s/Other_Information.txt).  
Current path: `Tongmyong_University/Graduate/Tongmyong_Master_s/Other_Information.txt`.  
Evidence: PDF pages 1, 2, 4, 10; 5 extracted record(s). Flags: `unmapped_or_ambiguous_topic`.

**Proposed action:** Keep R1 as source metadata; move R2 into the complete Application_Procedure; R3 into Documents_Verification; R4-R5 into the dated Apostille appendix with its heading restored.

**Justification:** The five records are a cover, two application steps, a China-specific academic-verification requirement, and continuation country lists. Those country lists are not nationality eligibility rules.


### Source: Tongmyong Bachelor_s.pdf

Source PDF: [Open the local document](../data/pdfs/Tongmyong%20Bachelor_s.pdf).


#### R011 - Other_Information.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Tongmyong_University/Undergraduate/Tongmyong_Bachelor_s/Other_Information.txt).  
Current path: `Tongmyong_University/Undergraduate/Tongmyong_Bachelor_s/Other_Information.txt`.  
Evidence: PDF pages 1; 1 extracted record(s). Flags: `unmapped_or_ambiguous_topic`.

**Proposed action:** Retain the cover title as source metadata and exclude the TXT fragment from standalone answer retrieval.

**Justification:** The sole record is the spring-2027 international undergraduate guide title. It contributes intake/identity context, not an independent answer passage.


### Source: 2027_1학기 영남이공대학교 외국인특별전형 모집요강(En).pdf

Source PDF: [Open the local document](../data/pdfs/2027_1%E1%84%92%E1%85%A1%E1%86%A8%E1%84%80%E1%85%B5%20%E1%84%8B%E1%85%A7%E1%86%BC%E1%84%82%E1%85%A1%E1%86%B7%E1%84%8B%E1%85%B5%E1%84%80%E1%85%A9%E1%86%BC%E1%84%83%E1%85%A2%E1%84%92%E1%85%A1%E1%86%A8%E1%84%80%E1%85%AD%20%E1%84%8B%E1%85%AC%E1%84%80%E1%85%AE%E1%86%A8%E1%84%8B%E1%85%B5%E1%86%AB%E1%84%90%E1%85%B3%E1%86%A8%E1%84%87%E1%85%A7%E1%86%AF%E1%84%8C%E1%85%A5%E1%86%AB%E1%84%92%E1%85%A7%E1%86%BC%20%E1%84%86%E1%85%A9%E1%84%8C%E1%85%B5%E1%86%B8%E1%84%8B%E1%85%AD%E1%84%80%E1%85%A1%E1%86%BC%28En%29.pdf).


#### R012 - Application_Deadlines.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_2027_1_en_pdf/Mixed/2027_1_En/Application_Deadlines.txt).  
Current path: `Unverified_2027_1_en_pdf/Mixed/2027_1_En/Application_Deadlines.txt`.  
Evidence: PDF pages 8; 1 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Yeungnam identity correction. Split p.8 policy, translation and address clauses into Admission_Policies, Documents_Verification and Contact_Information. Rebuild Application_Deadlines from the full p.3 timetable, including item 20.

**Justification:** The current file is not a complete schedule; it contains cancellation, notices, translation and delivery clauses. Actual round dates were placed under Interviews_Assessment.


#### R013 - Contact_Information.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_2027_1_en_pdf/Mixed/2027_1_En/Contact_Information.txt).  
Current path: `Unverified_2027_1_en_pdf/Mixed/2027_1_En/Contact_Information.txt`.  
Evidence: PDF pages 8; 1 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Yeungnam identity correction. Keep Global Admissions Team contacts; move the mailing-receipt email instruction to Application_Procedure and strip the footer.

**Justification:** The p.8 passage combines useful institutional contacts with a document-delivery instruction. Keep each in its proper retrieval context.


#### R014 - Documents_Identity.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_2027_1_en_pdf/Mixed/2027_1_En/Documents_Identity.txt).  
Current path: `Unverified_2027_1_en_pdf/Mixed/2027_1_En/Documents_Identity.txt`.  
Evidence: PDF pages 6; 1 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Yeungnam identity correction and rebuild the p.6 required-documents table. Split academic, identity, verification, financial and language evidence while retaining an overall Documents_Required checklist.

**Justification:** R1 crosses several document categories and ends mid-table. The continuations appear in items 18 and 16; row labels and conditions must be restored before classification.


#### R015 - Documents_Verification.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_2027_1_en_pdf/Mixed/2027_1_En/Documents_Verification.txt).  
Current path: `Unverified_2027_1_en_pdf/Mixed/2027_1_En/Documents_Verification.txt`.  
Evidence: PDF pages 9; 1 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Yeungnam identity correction. Keep Documents_Verification, rejoining the Apostille process and country-list continuations from item 21. Preserve guide date and attribution.

**Justification:** The p.9 appendix is the right subject, but process steps and countries are flattened and fragmented. It is a guide-specific reference, not independently current treaty-membership guidance.


#### R016 - Eligibility_Language.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_2027_1_en_pdf/Mixed/2027_1_En/Eligibility_Language.txt).  
Current path: `Unverified_2027_1_en_pdf/Mixed/2027_1_En/Eligibility_Language.txt`.  
Evidence: PDF pages 3, 11; 3 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Yeungnam identity correction. Separate p.3 Korean/English-track language rules, nationality/academic conditions, graduation rules and schedule material. Move p.11 blank language/housing fields to Application_Forms.

**Justification:** R1-R2 interleave columns of eligibility and schedule text. R3 is an application-form fragment, not a standalone language requirement.


#### R017 - Eligibility_Nationality.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_2027_1_en_pdf/Mixed/2027_1_En/Eligibility_Nationality.txt).  
Current path: `Unverified_2027_1_en_pdf/Mixed/2027_1_En/Eligibility_Nationality.txt`.  
Evidence: PDF pages 1; 1 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Yeungnam identity correction. Keep cover audience as metadata; rebuild Eligibility_Nationality from p.3. Remove promotional ranking text from the eligibility passage.

**Justification:** The sole p.1 record is mostly a cover. Its brief statement about foreign parents does not preserve the detailed nationality exceptions in the actual eligibility section.


#### R018 - Financial_Proof.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_2027_1_en_pdf/Mixed/2027_1_En/Financial_Proof.txt).  
Current path: `Unverified_2027_1_en_pdf/Mixed/2027_1_En/Financial_Proof.txt`.  
Evidence: PDF pages 6; 2 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Yeungnam identity correction. Keep financial evidence and conditional submission/exemption clauses under Financial_Proof; return photo, language and general-document rows to their own topics.

**Justification:** The p.6 records cross table rows. Financial exceptions and timing must remain attached to the relevant bank-evidence requirement, while neighboring photo/test rows should not inherit it.


#### R019 - Housing_Dormitory.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_2027_1_en_pdf/Mixed/2027_1_En/Housing_Dormitory.txt).  
Current path: `Unverified_2027_1_en_pdf/Mixed/2027_1_En/Housing_Dormitory.txt`.  
Evidence: PDF pages 7; 1 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Yeungnam identity correction. Rebuild p.7 housing rows with residence name, occupancy, monthly rate, annual equivalent, meal exclusions and payment period together.

**Justification:** The fragment labels Global House but lists annual totals for two residences. The source distinguishes Happy Dormitory and Global House; flattened text risks assigning the wrong cost.


#### R020 - Interviews_Assessment.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_2027_1_en_pdf/Mixed/2027_1_En/Interviews_Assessment.txt).  
Current path: `Unverified_2027_1_en_pdf/Mixed/2027_1_En/Interviews_Assessment.txt`.  
Evidence: PDF pages 3, 7; 2 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Yeungnam identity correction. Move p.3 round dates to Application_Deadlines. Split p.7 into Application_Procedure, Interviews_Assessment and Housing_Dormitory.

**Justification:** R1 is an interleaved timetable, while R2 contains process, screening and a dormitory heading. Restore round/event relationships before storing dates.


#### R021 - Other_Information.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_2027_1_en_pdf/Mixed/2027_1_En/Other_Information.txt).  
Current path: `Unverified_2027_1_en_pdf/Mixed/2027_1_En/Other_Information.txt`.  
Evidence: PDF pages 3, 4, 9, 10, 12, 13, 14, 15; 10 extracted record(s). Flags: `unmapped_or_ambiguous_topic`, `unverified_university`.

**Proposed action:** Apply the Yeungnam identity correction. Exclude R1-R2 footers; join R3-R4 to Apostille verification; place R5-R6 in forms, R7 in academic-record authorization, and R8-R10 in Privacy_Consent after Korean-language review.

**Justification:** The ten records mix footers, country lists, blank forms, authorization and Korean consent clauses. Do not assign a generic domain merely to make these flags disappear.


#### R022 - Programs_Majors.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_2027_1_en_pdf/Mixed/2027_1_En/Programs_Majors.txt).  
Current path: `Unverified_2027_1_en_pdf/Mixed/2027_1_En/Programs_Majors.txt`.  
Evidence: PDF pages 4; 1 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Yeungnam identity correction. Reconstruct the p.4 program table with item 25's continuation, preserving duration, track, quota exceptions and hierarchy.

**Justification:** The file contains only part of the catalog. Other program rows were placed in Visa_Immigration because a nearby footnote mentions visa holders.


#### R023 - Scholarships_Other.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_2027_1_en_pdf/Mixed/2027_1_En/Scholarships_Other.txt).  
Current path: `Unverified_2027_1_en_pdf/Mixed/2027_1_En/Scholarships_Other.txt`.  
Evidence: PDF pages 2, 5, 8; 4 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Yeungnam identity correction. Exclude R1's contents list. Split p.5 actual tuition, entrance scholarships and continuing-student scholarships, including item 24. Split p.8 insurance/refund/policy columns into their own topics.

**Justification:** The real tuition table sits in R2 before scholarship data. R4 interleaves multiple columns. The whole file cannot safely be treated as scholarships.


#### R024 - Tuition_Fees.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_2027_1_en_pdf/Mixed/2027_1_En/Tuition_Fees.txt).  
Current path: `Unverified_2027_1_en_pdf/Mixed/2027_1_En/Tuition_Fees.txt`.  
Evidence: PDF pages 5; 1 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Yeungnam identity correction. Merge the existing fragment into continuing-student scholarships. Rebuild Tuition_Fees from section A on p.5, currently in item 23.

**Justification:** The entire record consists of GPA bands and percentage tuition reductions, not tuition prices. This is a confirmed topic mismatch.


#### R025 - Visa_Immigration.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_2027_1_en_pdf/Mixed/2027_1_En/Visa_Immigration.txt).  
Current path: `Unverified_2027_1_en_pdf/Mixed/2027_1_En/Visa_Immigration.txt`.  
Evidence: PDF pages 4; 1 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Yeungnam identity correction. Merge most of the record into Programs_Majors; preserve the work-study/visa-holder footnote with the programs it qualifies.

**Justification:** The p.4 record is predominantly program names, durations and English-track availability. A footnote about employment-visa holders does not make this general visa guidance or student-work authorization.


### Source: 2.ENG2027-SpringSemesterFreshmanTransferAdmissionGuideline.pdf

Source PDF: [Open the local document](../data/pdfs/2.ENG2027-SpringSemesterFreshmanTransferAdmissionGuideline.pdf).


#### R026 - Application_Deadlines.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_2_eng2027_springsemesterfreshmantransferadmissionguideline_pdf/Mixed/2_ENG2027_SpringSemesterFreshmanTransferAdmissionGuideline/Application_Deadlines.txt).  
Current path: `Unverified_2_eng2027_springsemesterfreshmantransferadmissionguideline_pdf/Mixed/2_ENG2027_SpringSemesterFreshmanTransferAdmissionGuideline/Application_Deadlines.txt`.  
Evidence: PDF pages 8; 1 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Gachon identity and undergraduate-scope correction. Retain Application_Deadlines after rebuilding p.8 as an intake-by-event table; reconnect item 35 R4's cancellation fragment.

**Justification:** First, second and third intake dates are interleaved. The table columns are needed to identify which event each date belongs to.


#### R027 - Application_Fee.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_2_eng2027_springsemesterfreshmantransferadmissionguideline_pdf/Mixed/2_ENG2027_SpringSemesterFreshmanTransferAdmissionGuideline/Application_Fee.txt).  
Current path: `Unverified_2_eng2027_springsemesterfreshmantransferadmissionguideline_pdf/Mixed/2_ENG2027_SpringSemesterFreshmanTransferAdmissionGuideline/Application_Fee.txt`.  
Evidence: PDF pages 2, 12; 2 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Gachon identity correction. Exclude R1's contents fragment; retain p.12 fee/refund clauses, separating any evaluation rows that follow.

**Justification:** R1 is navigation. R2 contains the actual fee rule and cancellation/refund conditions; a contents heading is not evidence of an amount.


#### R028 - Application_Procedure.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_2_eng2027_springsemesterfreshmantransferadmissionguideline_pdf/Mixed/2_ENG2027_SpringSemesterFreshmanTransferAdmissionGuideline/Application_Procedure.txt).  
Current path: `Unverified_2_eng2027_springsemesterfreshmantransferadmissionguideline_pdf/Mixed/2_ENG2027_SpringSemesterFreshmanTransferAdmissionGuideline/Application_Procedure.txt`.  
Evidence: PDF pages 11; 1 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Gachon identity correction. Move the record to portfolio requirements under Documents_Required or Interviews_Assessment and reconnect the beginning of p.11's arts/music table. Build general application instructions separately from p.15.

**Justification:** The current Application_Procedure record describes artwork and music-performance videos, not the general application workflow, and begins mid-instruction.


#### R029 - Documents_Identity.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_2_eng2027_springsemesterfreshmantransferadmissionguideline_pdf/Mixed/2_ENG2027_SpringSemesterFreshmanTransferAdmissionGuideline/Documents_Identity.txt).  
Current path: `Unverified_2_eng2027_springsemesterfreshmantransferadmissionguideline_pdf/Mixed/2_ENG2027_SpringSemesterFreshmanTransferAdmissionGuideline/Documents_Identity.txt`.  
Evidence: PDF pages 10; 1 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Gachon identity correction. Reconstruct p.10's document table; keep applicant/parent ID rows here and move statement-of-purpose and print/sign instructions into their proper topics.

**Justification:** The record spans several document categories. Preserve the document-count and applicant-type columns before splitting.


#### R030 - Documents_Verification.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_2_eng2027_springsemesterfreshmantransferadmissionguideline_pdf/Mixed/2_ENG2027_SpringSemesterFreshmanTransferAdmissionGuideline/Documents_Verification.txt).  
Current path: `Unverified_2_eng2027_springsemesterfreshmantransferadmissionguideline_pdf/Mixed/2_ENG2027_SpringSemesterFreshmanTransferAdmissionGuideline/Documents_Verification.txt`.  
Evidence: PDF pages 11; 2 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Gachon identity correction. Keep Documents_Verification after restoring certificate/transcript headings and applicant-specific columns from pp.10-11.

**Justification:** The two records are relevant authentication instructions, but begin in the middle of table rows and depend on the preceding context for what must be certified.


#### R031 - Eligibility_Language.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_2_eng2027_springsemesterfreshmantransferadmissionguideline_pdf/Mixed/2_ENG2027_SpringSemesterFreshmanTransferAdmissionGuideline/Eligibility_Language.txt).  
Current path: `Unverified_2_eng2027_springsemesterfreshmantransferadmissionguideline_pdf/Mixed/2_ENG2027_SpringSemesterFreshmanTransferAdmissionGuideline/Eligibility_Language.txt`.  
Evidence: PDF pages 3, 5, 6, 7, 9, 15; 6 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Gachon identity correction. Move program rows from pp.3 and 5-7 into Programs_Majors with department-specific language notes. Keep p.9 entry-language rules; separate p.15 post-entry/graduation obligations.

**Justification:** Four records are principally program tables selected because they mention TOPIK or English tracks. Entry requirements and graduation requirements are not interchangeable thresholds.


#### R032 - Eligibility_Nationality.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_2_eng2027_springsemesterfreshmantransferadmissionguideline_pdf/Mixed/2_ENG2027_SpringSemesterFreshmanTransferAdmissionGuideline/Eligibility_Nationality.txt).  
Current path: `Unverified_2_eng2027_springsemesterfreshmantransferadmissionguideline_pdf/Mixed/2_ENG2027_SpringSemesterFreshmanTransferAdmissionGuideline/Eligibility_Nationality.txt`.  
Evidence: PDF pages 9; 1 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Gachon identity correction. Split p.9 into nationality, academic and language eligibility, preserving freshman, second-year transfer and third-year transfer columns.

**Justification:** The single record mixes parental citizenship and acquisition timing with schooling and transfer credits. Its nationality label hides the academic conditions.


#### R033 - Financial_Proof.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_2_eng2027_springsemesterfreshmantransferadmissionguideline_pdf/Mixed/2_ENG2027_SpringSemesterFreshmanTransferAdmissionGuideline/Financial_Proof.txt).  
Current path: `Unverified_2_eng2027_springsemesterfreshmantransferadmissionguideline_pdf/Mixed/2_ENG2027_SpringSemesterFreshmanTransferAdmissionGuideline/Financial_Proof.txt`.  
Evidence: PDF pages 10; 1 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Gachon identity correction. Keep bank evidence and timing/account-owner conditions under Financial_Proof; move the leading portfolio and trailing language-document fragments into their correct topics.

**Justification:** The p.10 extract crosses required-document table rows. The financial rule is present but should not carry unrelated neighboring requirements.


#### R034 - Housing_Dormitory.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_2_eng2027_springsemesterfreshmantransferadmissionguideline_pdf/Mixed/2_ENG2027_SpringSemesterFreshmanTransferAdmissionGuideline/Housing_Dormitory.txt).  
Current path: `Unverified_2_eng2027_springsemesterfreshmantransferadmissionguideline_pdf/Mixed/2_ENG2027_SpringSemesterFreshmanTransferAdmissionGuideline/Housing_Dormitory.txt`.  
Evidence: PDF pages 17, 18; 2 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Gachon identity correction. Move p.17's admissions-team block to Contact_Information; retain p.18 housing material after reconstructing its application sequence and diagram labels.

**Justification:** R1 is the university contact section followed by appendix headings. R2 is a dormitory process fragment, not evidence of prices or room availability.


#### R035 - Other_Information.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_2_eng2027_springsemesterfreshmantransferadmissionguideline_pdf/Mixed/2_ENG2027_SpringSemesterFreshmanTransferAdmissionGuideline/Other_Information.txt).  
Current path: `Unverified_2_eng2027_springsemesterfreshmantransferadmissionguideline_pdf/Mixed/2_ENG2027_SpringSemesterFreshmanTransferAdmissionGuideline/Other_Information.txt`.  
Evidence: PDF pages 1, 4, 6, 8, 9, 15, 16; 7 extracted record(s). Flags: `unmapped_or_ambiguous_topic`, `unverified_university`.

**Proposed action:** Apply the Gachon identity correction. Keep R1 as metadata; merge R2-R3 into program tables; reconnect R4 to the deadline note; move R5 to transfer Eligibility_Academic; split R6-R7 into graduation obligations, admission policies and language precedence.

**Justification:** These seven records are identifiable continuations from other sections. Retire the generic topic only after each continuation is joined to its proper source context.


#### R036 - Programs_Majors.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_2_eng2027_springsemesterfreshmantransferadmissionguideline_pdf/Mixed/2_ENG2027_SpringSemesterFreshmanTransferAdmissionGuideline/Programs_Majors.txt).  
Current path: `Unverified_2_eng2027_springsemesterfreshmantransferadmissionguideline_pdf/Mixed/2_ENG2027_SpringSemesterFreshmanTransferAdmissionGuideline/Programs_Majors.txt`.  
Evidence: PDF pages 3, 4, 5, 7; 5 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Gachon identity correction. Reconstruct complete pp.3-7 program/track tables with fragments from items 31 and 35. Separate transfer credit recognition and additional-course obligations into academic/degree-requirement records.

**Justification:** The records mix program rows, major-selection restrictions, language courses and credit recognition. Preserve campus, freshman/transfer and teaching-track distinctions.


#### R037 - Scholarships_Other.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_2_eng2027_springsemesterfreshmantransferadmissionguideline_pdf/Mixed/2_ENG2027_SpringSemesterFreshmanTransferAdmissionGuideline/Scholarships_Other.txt).  
Current path: `Unverified_2_eng2027_springsemesterfreshmantransferadmissionguideline_pdf/Mixed/2_ENG2027_SpringSemesterFreshmanTransferAdmissionGuideline/Scholarships_Other.txt`.  
Evidence: PDF pages 2, 13, 14; 5 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Gachon identity correction. Remove contents material. Reconstruct entrance and enrolled-student scholarships separately, restoring GPA/language columns and item 38 R3's continuation. Preserve exclusions and one-time conditions.

**Justification:** The continuing-student scholarship table was split across this file and Tuition_Fees. Benefits cannot be interpreted safely without eligibility conditions and exclusions.


#### R038 - Tuition_Fees.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_2_eng2027_springsemesterfreshmantransferadmissionguideline_pdf/Mixed/2_ENG2027_SpringSemesterFreshmanTransferAdmissionGuideline/Tuition_Fees.txt).  
Current path: `Unverified_2_eng2027_springsemesterfreshmantransferadmissionguideline_pdf/Mixed/2_ENG2027_SpringSemesterFreshmanTransferAdmissionGuideline/Tuition_Fees.txt`.  
Evidence: PDF pages 10, 12, 14, 15, 16; 6 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Gachon identity correction. Keep the p.12 price table with its explicit 2026-fall basis. Move R1 to family-document requirements, R3 to scholarships, R4 to application procedures and R5-R6 to admission/refund policies. Separate evaluation text from tuition.

**Justification:** These six records are not a coherent tuition file. The source describes displayed fees as a prior-semester reference subject to change, not verified 2027 prices.


### Source: Graduate.pdf

Source PDF: [Open the local document](../data/pdfs/Graduate.pdf).


#### R039 - Application_Deadlines.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_graduate_pdf/Graduate/Graduate/Application_Deadlines.txt).  
Current path: `Unverified_graduate_pdf/Graduate/Graduate/Application_Deadlines.txt`.  
Evidence: PDF pages 12; 1 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Kongju graduate identity correction. Split the p.12 fragment into application/submission instructions and its deadline clauses; rebuild the actual schedule from p.3, currently in item 51.

**Justification:** The file begins with online help and physical-document delivery instructions rather than the main admissions timetable.


#### R040 - Application_Fee.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_graduate_pdf/Graduate/Graduate/Application_Fee.txt).  
Current path: `Unverified_graduate_pdf/Graduate/Graduate/Application_Fee.txt`.  
Evidence: PDF pages 2, 8, 12; 3 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Kongju graduate identity correction. Remove contents material. Retain p.8 fee/refund conditions; separate document-screening criteria and p.12 application-completion clauses into assessment/procedure topics.

**Justification:** The file mixes navigation, actual fee/screening rules and workflow. Graduate assessment is document review here; the generic assessment topic must not imply a required interview.


#### R041 - Application_Procedure.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_graduate_pdf/Graduate/Graduate/Application_Procedure.txt).  
Current path: `Unverified_graduate_pdf/Graduate/Graduate/Application_Procedure.txt`.  
Evidence: PDF pages 11; 1 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Kongju graduate identity correction. Reconstruct the full numbered workflow across pp.11-12 and retain the mailing address as a linked contact reference.

**Justification:** The extract starts at step 5 and jumps between steps and an address. Restoring sequence is necessary before presenting it as instructions.


#### R042 - Contact_Information.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_graduate_pdf/Graduate/Graduate/Contact_Information.txt).  
Current path: `Unverified_graduate_pdf/Graduate/Graduate/Contact_Information.txt`.  
Evidence: PDF pages 3, 23; 2 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Kongju graduate identity correction. Move R1 to Application_Procedure and R2 to application forms/declarations. Rebuild institutional contacts from pp.18-20 using items 52 and 54.

**Justification:** Neither record is the university directory: one concerns the applicant's own contact details; the other asks about a previously attended institution on a form.


#### R043 - Documents_Identity.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_graduate_pdf/Graduate/Graduate/Documents_Identity.txt).  
Current path: `Unverified_graduate_pdf/Graduate/Graduate/Documents_Identity.txt`.  
Evidence: PDF pages 8, 10, 11, 21, 22; 7 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Kongju graduate identity correction. Retain R1-R3 identity/family evidence; move R4-R5 to Financial_Proof; split R6's general checklist; place R7 in Application_Forms.

**Justification:** Identity evidence is mixed with bank and guarantor conditions, a checklist and a blank application form. Reconstruct the document-table rows before extracting requirements.


#### R044 - Documents_Required.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_graduate_pdf/Graduate/Graduate/Documents_Required.txt).  
Current path: `Unverified_graduate_pdf/Graduate/Graduate/Documents_Required.txt`.  
Evidence: PDF pages 2, 14; 2 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Kongju graduate identity correction. Remove contents material; move R2 to dormitory selection/contacts; rebuild Documents_Required from pp.8-9 and p.21's actual checklist.

**Justification:** The substantive p.14 passage concerns dormitory supporting documents, not the complete university admission checklist.


#### R045 - Documents_Verification.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_graduate_pdf/Graduate/Graduate/Documents_Verification.txt).  
Current path: `Unverified_graduate_pdf/Graduate/Graduate/Documents_Verification.txt`.  
Evidence: PDF pages 9, 10, 13, 21; 7 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Kongju graduate identity correction. Retain complete academic-authentication and country-specific rules; move p.21 finance/residence-card checklist fragments to their own topics.

**Justification:** Most pp.9-10 material fits the label, but the final checklist fragment includes other requirements. Preserve exceptions, headings and guide-specific dates instead of treating every line as academic verification.


#### R046 - Eligibility_Language.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_graduate_pdf/Graduate/Graduate/Eligibility_Language.txt).  
Current path: `Unverified_graduate_pdf/Graduate/Graduate/Eligibility_Language.txt`.  
Evidence: PDF pages 7, 8, 13, 21, 22, 23; 11 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Kongju graduate identity correction. Rebuild language rules by department, degree and track from pp.6-8. Separate general document lists, blank form fields, registration obligations and graduation-language rules.

**Justification:** The 11 records mix entry scores, department exceptions, graduation evidence and forms. Preserve rules that must be met together versus alternatives rather than reduce them to one score threshold.


#### R047 - Eligibility_Nationality.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_graduate_pdf/Graduate/Graduate/Eligibility_Nationality.txt).  
Current path: `Unverified_graduate_pdf/Graduate/Graduate/Eligibility_Nationality.txt`.  
Evidence: PDF pages 6, 10; 3 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Kongju graduate identity correction. Rejoin and retain the nationality clause; move consultation contacts to Contact_Information, academic-degree rules to Eligibility_Academic, and Apostille-country lists to Documents_Verification.

**Justification:** The file begins with staff details and ends with authentication-country lists. Those countries are not a list of eligible applicant nationalities.


#### R048 - Financial_Proof.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_graduate_pdf/Graduate/Graduate/Financial_Proof.txt).  
Current path: `Unverified_graduate_pdf/Graduate/Graduate/Financial_Proof.txt`.  
Evidence: PDF pages 9, 11, 27; 4 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Kongju graduate identity correction. Reassemble financial rules with bank passages in items 43 and 55 and forms in items 49 and 52. Separate general document handling while preserving sponsor and shortfall conditions.

**Justification:** Financial requirements are scattered. R2 is general handling, while R3-R4 contain conditional professor sponsorship and support-shortfall requirements.


#### R049 - Health_Insurance.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_graduate_pdf/Graduate/Graduate/Health_Insurance.txt).  
Current path: `Unverified_graduate_pdf/Graduate/Graduate/Health_Insurance.txt`.  
Evidence: PDF pages 26; 1 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Kongju graduate identity correction. Move the whole record to Financial_Proof with form metadata. Rebuild Health_Insurance from p.17, currently captured in item 54.

**Justification:** The source p.26 is Form 5, Affidavit of Financial Support. Medical insurance is mentioned only as one sponsored expense, not as an insurance-enrollment rule.


#### R050 - Housing_Dormitory.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_graduate_pdf/Graduate/Graduate/Housing_Dormitory.txt).  
Current path: `Unverified_graduate_pdf/Graduate/Graduate/Housing_Dormitory.txt`.  
Evidence: PDF pages 12, 14; 3 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Kongju graduate identity correction. Move R1's data-use clause to Privacy_Consent; reconstruct R2-R3 as campus/residence/room/meal/deposit fee rows with their 2026-fall reference date.

**Justification:** The p.12 record merely mentions dormitory selection as a data-use purpose. Real dormitory charges are on p.14; their flattened columns risk incorrect price-to-room assignments.


#### R051 - Interviews_Assessment.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_graduate_pdf/Graduate/Graduate/Interviews_Assessment.txt).  
Current path: `Unverified_graduate_pdf/Graduate/Graduate/Interviews_Assessment.txt`.  
Evidence: PDF pages 3; 1 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Kongju graduate identity correction. Rebuild p.3 as Application_Deadlines. Retain its complete assessment-method statement separately and compare it with p.8.

**Justification:** The record is mainly an admissions timeline and explicitly says document evaluation with no in-person interviews. Its current label can lead to the wrong assessment assumption.


#### R052 - Other_Information.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_graduate_pdf/Graduate/Graduate/Other_Information.txt).  
Current path: `Unverified_graduate_pdf/Graduate/Graduate/Other_Information.txt`.  
Evidence: PDF pages 1, 4, 5, 6, 7, 10, 11, 17, 18, 19, 20, 21, 23, 24, 25, 27; 23 extracted record(s). Flags: `unmapped_or_ambiguous_topic`, `unverified_university`.

**Proposed action:** Apply the Kongju graduate identity correction. Keep R1 as metadata; move R2-R6 to programs; R7 and R12-R19 to contacts; R8 to academic eligibility/deadlines; R9 to verification; R10 to policies; R11 to Student_Support; R20 to consent; R21-R22 to form instructions; R23 to financial proof.

**Justification:** The 23 records mix departments, contacts, degree-completion conditions, country-list continuations, buddy/cultural services and forms. The p.17 support passage supplies actual Culture & life material currently missed by the mapping.


#### R053 - Programs_Majors.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_graduate_pdf/Graduate/Graduate/Programs_Majors.txt).  
Current path: `Unverified_graduate_pdf/Graduate/Graduate/Programs_Majors.txt`.  
Evidence: PDF pages 4, 6, 7, 15; 4 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Kongju graduate identity correction. Rebuild the pp.4-5 catalog using item 52; move consultation contacts to contacts/application guidance, degree eligibility to Eligibility_Academic, and the p.15 research-scholarship continuation back into its table.

**Justification:** Only part of this file is a program catalog. Contacts, entry-degree conditions and research-scholarship participation belong to different subjects.


#### R054 - Scholarships_Other.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_graduate_pdf/Graduate/Graduate/Scholarships_Other.txt).  
Current path: `Unverified_graduate_pdf/Graduate/Graduate/Scholarships_Other.txt`.  
Evidence: PDF pages 2, 12, 15, 16, 17, 18; 14 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Kongju graduate identity correction. Remove contents material. Separate results/registration, tuition, contacts, health insurance and student support from scholarships. Reconstruct each BK21 program's eligibility, amount and duration across pp.15-17.

**Justification:** The file holds the true graduate tuition table and insurance section as well as research scholarships. Awards are conditional on participating departments and study stage, not generic benefits for all students.


#### R055 - Tuition_Fees.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_graduate_pdf/Graduate/Graduate/Tuition_Fees.txt).  
Current path: `Unverified_graduate_pdf/Graduate/Graduate/Tuition_Fees.txt`.  
Evidence: PDF pages 3, 11, 13; 3 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Kongju graduate identity correction. Move payment notices to registration guidance, financial-evidence timing to Financial_Proof and selection/non-registration clauses to Admission_Policies. Rebuild tuition prices from p.15, currently in item 54.

**Justification:** None of these three fragments is the complete tuition-price table. Mentioning tuition in payment or visa-document conditions does not make the passage a price record.


### Source: Undergraduate.pdf

Source PDF: [Open the local document](../data/pdfs/Undergraduate.pdf).


#### R056 - Application_Deadlines.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_undergraduate_pdf/Undergraduate/Undergraduate/Application_Deadlines.txt).  
Current path: `Unverified_undergraduate_pdf/Undergraduate/Undergraduate/Application_Deadlines.txt`.  
Evidence: PDF pages 11; 1 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Kongju undergraduate identity correction. Keep the delivery-method/address clause in Application_Procedure; rebuild the full timetable from p.3, currently spread across items 69 and 73.

**Justification:** The p.11 record concerns physical-document delivery and is insufficient as the main deadline record.


#### R057 - Application_Fee.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_undergraduate_pdf/Undergraduate/Undergraduate/Application_Fee.txt).  
Current path: `Unverified_undergraduate_pdf/Undergraduate/Undergraduate/Application_Fee.txt`.  
Evidence: PDF pages 2, 6, 7, 11; 5 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Kongju undergraduate identity correction. Remove contents material. Split language and disciplinary/scoring passages into their proper topics, retain the actual fee/refund section and move workflow text to Application_Procedure.

**Justification:** The five records combine multiple sections. Reconstruct pp.6-7 to distinguish fee conditions from screening criteria rather than assuming everything near the heading is a fee rule.


#### R058 - Application_Procedure.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_undergraduate_pdf/Undergraduate/Undergraduate/Application_Procedure.txt).  
Current path: `Unverified_undergraduate_pdf/Undergraduate/Undergraduate/Application_Procedure.txt`.  
Evidence: PDF pages 11; 1 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Kongju undergraduate identity correction. Retain Application_Procedure after restoring the original sequence and joining item 57 R5 and item 56's relevant submission detail.

**Justification:** The source diagram was read out of order; the extracted sequence starts 1, 3, 2, 4. Copying it unchanged would produce confusing instructions.


#### R059 - Contact_Information.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_undergraduate_pdf/Undergraduate/Undergraduate/Contact_Information.txt).  
Current path: `Unverified_undergraduate_pdf/Undergraduate/Undergraduate/Contact_Information.txt`.  
Evidence: PDF pages 3, 12, 17, 19; 4 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Kongju undergraduate identity correction. Move applicant obligations to procedures, p.12 results/registration and consent into their own topics, p.19 form fields into forms; retain p.17 directory rows with campus/phone-prefix headers restored.

**Justification:** Applicant contact fields are not admissions-office contacts. The actual directory needs area codes and campus labels attached to the extensions.


#### R060 - Documents_Academic.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_undergraduate_pdf/Undergraduate/Undergraduate/Documents_Academic.txt).  
Current path: `Unverified_undergraduate_pdf/Undergraduate/Undergraduate/Documents_Academic.txt`.  
Evidence: PDF pages 18; 1 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Kongju undergraduate identity correction. Keep academic-document checklist content, separating freshman, transfer and graduate rows and their degree scope.

**Justification:** The p.18 checklist mentions multiple courses even though this is the undergraduate guide. Graduate documents must not automatically become undergraduate requirements.


#### R061 - Documents_Identity.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_undergraduate_pdf/Undergraduate/Undergraduate/Documents_Identity.txt).  
Current path: `Unverified_undergraduate_pdf/Undergraduate/Undergraduate/Documents_Identity.txt`.  
Evidence: PDF pages 8, 10, 11, 19, 20; 8 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Kongju undergraduate identity correction. Retain identity/family evidence; move academic records to Documents_Academic, bank/guarantor clauses to Financial_Proof and name-formatting/form checklists into appropriate application topics.

**Justification:** The eight records cross academic, identity, finance and form sections. Family identity and financial sponsorship are different topics despite sharing references to relatives.


#### R062 - Documents_Required.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_undergraduate_pdf/Undergraduate/Undergraduate/Documents_Required.txt).  
Current path: `Unverified_undergraduate_pdf/Undergraduate/Undergraduate/Documents_Required.txt`.  
Evidence: PDF pages 2, 13; 2 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Kongju undergraduate identity correction. Remove contents material; move dormitory selection/contacts to accommodation/contact records; rebuild the admissions checklist from pp.7-8 and p.18.

**Justification:** The only substantive record concerns dormitory supporting documents rather than the main university application checklist.


#### R063 - Documents_Verification.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_undergraduate_pdf/Undergraduate/Undergraduate/Documents_Verification.txt).  
Current path: `Unverified_undergraduate_pdf/Undergraduate/Undergraduate/Documents_Verification.txt`.  
Evidence: PDF pages 5, 8, 9, 12, 18; 9 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Kongju undergraduate identity correction. Keep authentication and China-specific evidence with complete table headers. Separate course-language notes, bank/residence requirements and unrelated admission consequences.

**Justification:** Useful certification rules are mixed with adjacent topics. The China-document table must preserve school-type rows and alternative accepted evidence, not collapse everything into a single requirement.


#### R064 - Eligibility_Language.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_undergraduate_pdf/Undergraduate/Undergraduate/Eligibility_Language.txt).  
Current path: `Unverified_undergraduate_pdf/Undergraduate/Undergraduate/Eligibility_Language.txt`.  
Evidence: PDF pages 5, 6, 7, 8, 12, 18; 7 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Kongju undergraduate identity correction. Reconstruct language requirements by general versus International Studies track, separating transfer academics, graduation obligations, program rows and blank checklist fields.

**Justification:** The seven records mix entry and graduation thresholds. Preserve simultaneous conditions versus alternatives; do not summarize them as one universal test-score requirement.


#### R065 - Eligibility_Nationality.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_undergraduate_pdf/Undergraduate/Undergraduate/Eligibility_Nationality.txt).  
Current path: `Unverified_undergraduate_pdf/Undergraduate/Undergraduate/Eligibility_Nationality.txt`.  
Evidence: PDF pages 6, 20; 2 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Kongju undergraduate identity correction. Keep nationality rules and citizenship-timing conditions, separating academic qualifications. Move the p.20 transfer form to Application_Forms.

**Justification:** A nationality field on a blank transfer application is not an admission rule. The first record contains actual eligibility; the second serves a different purpose.


#### R066 - Financial_Proof.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_undergraduate_pdf/Undergraduate/Undergraduate/Financial_Proof.txt).  
Current path: `Unverified_undergraduate_pdf/Undergraduate/Undergraduate/Financial_Proof.txt`.  
Evidence: PDF pages 8, 10, 22; 4 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Kongju undergraduate identity correction. Reassemble financial evidence with items 61 and 73. Preserve professor sponsorship and shortfall conditions; separate document-handling and residence-card rows.

**Justification:** The current financial file contains only part of the rule and includes unrelated packing/translation instructions. Financial prerequisites and exceptions need to be reunited.


#### R067 - Health_Insurance.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_undergraduate_pdf/Undergraduate/Undergraduate/Health_Insurance.txt).  
Current path: `Unverified_undergraduate_pdf/Undergraduate/Undergraduate/Health_Insurance.txt`.  
Evidence: PDF pages 21; 1 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Kongju undergraduate identity correction. Move this form to Financial_Proof. Rebuild Health_Insurance from p.14's insurance section, including the text now in item 72.

**Justification:** The source p.21 is Form 4, Affidavit of Financial Support. Insurance is listed as a sponsored expense. This is the same classification error seen in graduate item 49.


#### R068 - Housing_Dormitory.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_undergraduate_pdf/Undergraduate/Undergraduate/Housing_Dormitory.txt).  
Current path: `Unverified_undergraduate_pdf/Undergraduate/Undergraduate/Housing_Dormitory.txt`.  
Evidence: PDF pages 13; 2 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Kongju undergraduate identity correction. Retain housing information after reconstructing p.13's rows and campus-specific conditions. Preserve the 2026-fall reference date and change notice.

**Justification:** The fragments span room types, management fees, meals, totals and conditional extras. Flattened columns cannot safely serve as confirmed current room prices.


#### R069 - Interviews_Assessment.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_undergraduate_pdf/Undergraduate/Undergraduate/Interviews_Assessment.txt).  
Current path: `Unverified_undergraduate_pdf/Undergraduate/Undergraduate/Interviews_Assessment.txt`.  
Evidence: PDF pages 3, 6, 7; 3 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Kongju undergraduate identity correction. Move the p.3 timetable to Application_Deadlines; keep pp.6-7 assessment/interview/scoring rules with their applicable conditions.

**Justification:** This undergraduate guide does include interview-related content, unlike the graduate guide. Sharing the Kongju institution name must not erase that distinction.


#### R070 - Other_Information.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_undergraduate_pdf/Undergraduate/Undergraduate/Other_Information.txt).  
Current path: `Unverified_undergraduate_pdf/Undergraduate/Undergraduate/Other_Information.txt`.  
Evidence: PDF pages 1, 9, 15, 16, 18, 19, 20, 22; 9 extracted record(s). Flags: `unmapped_or_ambiguous_topic`, `unverified_university`.

**Proposed action:** Apply the Kongju undergraduate identity correction. Keep R1 as metadata, R2-R3 under Apostille verification, R4-R6 as reconstructed contacts/address records and R7-R9 under financial support/forms.

**Justification:** The file mixes a cover, country lists, directories and declarations. R7-R8 include conditional financial wording that should not be discarded with empty form fields.


#### R071 - Programs_Majors.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_undergraduate_pdf/Undergraduate/Undergraduate/Programs_Majors.txt).  
Current path: `Unverified_undergraduate_pdf/Undergraduate/Undergraduate/Programs_Majors.txt`.  
Evidence: PDF pages 4, 5, 15, 16; 6 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Kongju undergraduate identity correction. Rebuild program availability across pp.4-5 with related fragments in items 63 and 64. Move pp.15-16 directories to Contact_Information, retaining campus/area-code headers.

**Justification:** The first records describe programs while the last three list phone numbers and websites. A directory entry is not proof that a particular admission route is open.


#### R072 - Scholarships_Other.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_undergraduate_pdf/Undergraduate/Undergraduate/Scholarships_Other.txt).  
Current path: `Unverified_undergraduate_pdf/Undergraduate/Undergraduate/Scholarships_Other.txt`.  
Evidence: PDF pages 2, 12, 14, 15; 5 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Kongju undergraduate identity correction. Remove contents material. Separate Privacy_Consent, reconstruct p.14 scholarships with item 73's continuation, recover health insurance and Student_Support, and move p.15 institutional contacts into the directory.

**Justification:** Scholarship, insurance, support and contact sections are adjacent in the PDF. Their merger under one label hides actual student-life services and misroutes insurance questions.


#### R073 - Tuition_Fees.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Unverified_undergraduate_pdf/Undergraduate/Undergraduate/Tuition_Fees.txt).  
Current path: `Unverified_undergraduate_pdf/Undergraduate/Undergraduate/Tuition_Fees.txt`.  
Evidence: PDF pages 3, 10, 12, 14; 4 extracted record(s). Flags: `unverified_university`.

**Proposed action:** Apply the Kongju undergraduate identity correction. Reconstruct the real p.14 tuition table with its explicit 2026 basis; join scholarship rows into item 72; move result/payment dates, financial-evidence timing and admissions obligations into their own topics.

**Justification:** Only p.14 is the principal price section. The remaining records discuss payment events and evidence requirements, not tuition amounts.


### Source: Why WSU SPRING27 _FLYERS - Korean Track.pdf

Source PDF: [Open the local document](../data/pdfs/Why%20WSU%20SPRING27%20_FLYERS%20-%20Korean%20Track.pdf).


#### R074 - Other_Information.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Woosong_University/Mixed/Why_WSU_SPRING27_FLYERS_Korean_Track/Other_Information.txt).  
Current path: `Woosong_University/Mixed/Why_WSU_SPRING27_FLYERS_Korean_Track/Other_Information.txt`.  
Evidence: PDF pages 1; 1 extracted record(s). Flags: `unmapped_or_ambiguous_topic`.

**Proposed action:** Separate career-path phrases into Career_Support/program guidance and accreditation/rankings into attributed profile records after restoring their complete labels. Exclude incomplete ranking claims until then.

**Justification:** The p.1 extract mixes career roles with accreditation and ranking phrases. It does not establish student-work permission or identify a complete ranking position/category.


### Source: Woosong Brochure.pdf

Source PDF: [Open the local document](../data/pdfs/Woosong%20Brochure.pdf).


#### R075 - Other_Information.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Woosong_University/Mixed/Woosong_Brochure/Other_Information.txt).  
Current path: `Woosong_University/Mixed/Woosong_Brochure/Other_Information.txt`.  
Evidence: PDF pages 1, 2, 3, 8; 4 extracted record(s). Flags: `unmapped_or_ambiguous_topic`.

**Proposed action:** Keep slogans as metadata or exclude them. Separate Daejeon/campus context, institutional profile/rankings and the p.8 contact address. Verify numbers against the original layout before retaining them.

**Justification:** R1 is a slogan; R2 mixes mission and city context; R3 has interleaved ranking/partnership labels and numbers; R4 combines an address with an AI-image disclaimer. They should not become one undifferentiated factual profile.


### Source: Why WSU SPRING27 _FLYERS - undergradaute prgrams.pdf

Source PDF: [Open the local document](../data/pdfs/Why%20WSU%20SPRING27%20_FLYERS%20-%20undergradaute%20prgrams.pdf).


#### R076 - Other_Information.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Woosong_University/Undergraduate/Why_WSU_SPRING27_FLYERS_undergradaute_prgrams/Other_Information.txt).  
Current path: `Woosong_University/Undergraduate/Why_WSU_SPRING27_FLYERS_undergradaute_prgrams/Other_Information.txt`.  
Evidence: PDF pages 1; 1 extracted record(s). Flags: `unmapped_or_ambiguous_topic`.

**Proposed action:** Exclude the isolated ranking phrases until the flyer panel is reconstructed with position, publisher, year, subject and ranked entity. Retain complete claims only under attributed University_Rankings.

**Justification:** The only record refers to Global MBA and International Outlook in 2026 but omits key labels. A graduate-business ranking on an undergraduate flyer must not become the ranking of every undergraduate program.


### Source: Woosuk Bachelor_s.pdf

Source PDF: [Open the local document](../data/pdfs/Woosuk%20Bachelor_s.pdf).


#### R077 - Other_Information.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Woosuk_University/Undergraduate/Woosuk_Bachelor_s/Other_Information.txt).  
Current path: `Woosuk_University/Undergraduate/Woosuk_Bachelor_s/Other_Information.txt`.  
Evidence: PDF pages 1, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15, 16, 17, 19, 21, 24, 25, 26, 27, 30, 31, 35, 36, 38, 39, 40, 41, 42, 43, 44, 46, 47, 48, 49, 50, 53, 55, 59, 61; 69 extracted record(s). Flags: `unmapped_or_ambiguous_topic`.

**Proposed action:** Hold general/domestic-route content out of international-specific answers until applicability is established. Re-extract by section: registration policies, admission tracks/eligibility, program quotas, academic and practical-exam scoring, teacher training, housing and historical results. Exclude page noise and reconstruct numeric tables.

**Justification:** The 69 records span a machine-translated regular-admission guide, including CSAT, regional/rural and veteran/mature-student routes. These are not generic international conditions. P.59 marks housing values as 2026 references; p.61 is historical 2026 admissions results, not a current eligibility threshold.


#### R078 - Other_Policies.txt

File: [Open the current TXT file](../data/Randyll_Semantic_Knowledge/Randyll_Semantic_Knowledge/Woosuk_University/Undergraduate/Woosuk_Bachelor_s/Other_Policies.txt).  
Current path: `Woosuk_University/Undergraduate/Woosuk_Bachelor_s/Other_Policies.txt`.  
Evidence: PDF pages 4; 1 extracted record(s). Flags: `unmapped_or_ambiguous_topic`.

**Proposed action:** Reconnect the p.4 cancellation/selection disclaimer with its preceding clause; classify as Admission_Policies with item 77's audience restriction. Check the original-language wording before rewriting ambiguous score-related clauses.

**Justification:** The record begins with Cancellation and includes nondisclosure, suitability and responsibility clauses. Awkward machine translation must not be rewritten into an unsupported confident admission rule.

## Related issues that the present flags do not catch

The queue is a useful starting point, not a complete content-quality audit. A known topic can still contain the wrong subject, and a non-placeholder folder can still name the wrong kind of entity.

- **Ajou source ownership:** Item R007 establishes that `Korean_Language_Program` is an Ajou University brochure. Its related files should receive the same source-level correction, even if their current topics are mapped. Those additional files are outside the 78-item count.
- **Audience metadata:** The current schema does not enforce whether a rule applies to domestic applicants, international applicants, freshmen, transfers, a specific track, or a specific department. Add explicit audience/route metadata and retrieval checks before publishing mixed recruitment material. A domain tag alone cannot solve this.
- **Review and exclusion controls:** `review_required` currently records metadata concerns; it does not exclude a point from broad retrieval. Proposed holds and exclusions need a real ingestion/retrieval rule such as `retrieval_status`, plus tests. Changing a review label alone is insufficient.
- **Source-specific overrides:** Some ambiguous files require splitting rather than a global filename mapping. Do not change `Other_Information` or `Other_Policies` to one domain for the entire knowledge base. Keep explicit file/record-level review decisions with their source evidence.
- **Other files from repaired sources:** Reconstructing a source section may require moving passages from currently unflagged sibling files. The per-file recommendations name several such dependencies. Record every affected file in the implementation change log and preserve original passages.

## Proposed implementation batches after approval

| Batch | Work | Completion check |
|---|---|---|
| 1. Source identities | Correct Yeungnam, Gachon and both Kongju groups; include the explicit Ajou source-ownership correction if approved. Preserve separate degree/source identities. | No placeholder institution remains for those source groups; CSV, JSONL and TXT metadata agree; duplicate institution aliases do not arise. |
| 2. Clear classification errors | Repair the false insurance files, tuition/scholarship mix-ups, contact/form confusion, schedules and curriculum-as-policy cases. | Every moved passage has a destination and the original page/record reference; no facts vanish during merging. |
| 3. Table and section reconstruction | Rebuild program, intake, eligibility, price, scholarship, scoring and directory sections from the PDFs. Use layout-aware extraction or manual review where necessary. | Row/column relationships, currency, period, year, track, degree, exceptions and conjunctions match the source. Spot-check examples is not enough to sign off every numerical row. |
| 4. Content eligibility | Add source audience/route metadata, proposed topics, review status and actual exclusion rules; keep unresolved translation or promotional fragments out of ordinary answer retrieval. | Tests demonstrate that excluded passages cannot appear and domestic rules cannot silently answer international-specific requests. |
| 5. Fresh index and review tests | Build a new collection, validate it against the approved corrected manifest and compare representative retrieval results before switching the chat application. | Stored IDs/payloads match the approved corpus; old renamed/split records do not remain; the old collection is retained until acceptance. |

Original PDFs should remain unchanged. Keep a review ledger with old path/record, new destination, source page, reason, reviewer, review date and outcome. Corrections should change derived knowledge artifacts, not rewrite the supplied evidence.

The implementation should reconcile `KNOWLEDGE_INDEX.csv`, the prepared TXT files and `ALL_RECORDS.jsonl`. The active loader reads TXT and CSV; JSONL must still be kept consistent so a future ingestion path does not reintroduce the discarded classifications. Update the audit and the improvement guide only after the corrected dataset has passed validation.

## Acceptance checks for this review work

1. Each of R001–R078 has a recorded disposition: corrected, merged, excluded from active retrieval, or held with a reason. A held item must not be presented as verified.
2. Source identity, degree, intake and applicant scope survive file moves. Graduate and undergraduate Kongju rules remain separate.
3. Pure navigation, page headers and blank fields do not count as independent answer evidence. Meaningful conditions embedded in forms are retained with context.
4. Tuition prices are distinct from discounts, bank-balance evidence and housing charges. Historical/reference-year amounts remain explicitly dated.
5. Health-insurance answers retrieve the actual insurance section, not a financial guarantor's promise to pay expenses.
6. Program tables preserve degree availability and track restrictions; schedules preserve round/event relationships; contact directories preserve phone prefixes and campus labels.
7. Existing current facts are not silently changed into new values. Conflicting or unclear source wording is flagged instead of guessed.
8. Re-indexing does not leave obsolete IDs searchable. Test both focused and broad retrieval, because broad fallback currently includes review-flagged material.
9. A fresh audit and a small source-checked retrieval set demonstrate the corrected behavior. A zero-flag count alone is not an acceptance criterion.

**Approval boundary:** This report proposes the above work; it does not apply it. Approving only institution renames will resolve label errors but will leave the documented content-placement and extraction defects. Source/audience holds and excluding promotional/navigation fragments are included in the proposed corrective scope and remain pending approval.

Local TXT/PDF links require the project's ignored `data/` package to be present. No files have been published or committed as part of this report.

