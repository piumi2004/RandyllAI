CREATE OR REPLACE VIEW knowledge.import_review_summary AS
SELECT 'document passages'::text AS category, review_status, count(*) AS records
FROM knowledge.source_passages GROUP BY review_status
UNION ALL SELECT 'programmes',review_status,count(*) FROM university.academic_programs GROUP BY review_status
UNION ALL SELECT 'tuition figures',review_status,count(*) FROM financial.tuition_rates GROUP BY review_status
UNION ALL SELECT 'other costs',review_status,count(*) FROM financial.cost_items GROUP BY review_status
UNION ALL SELECT 'service statements',review_status,count(*) FROM agency.services GROUP BY review_status;

CREATE OR REPLACE VIEW financial.fee_review_queue AS
SELECT t.id,u.name AS university,t.field_of_study,t.degree_level,t.amount,t.amount_max,
       t.currency,t.billing_period,t.effective_year,t.is_estimate,t.extraction_status,
       t.review_status,s.document_name AS source_document,t.source_page,t.source_locator,
       t.review_notes,t.source_excerpt
FROM financial.tuition_rates t
JOIN university.universities u ON u.id=t.university_id
JOIN knowledge.sources s ON s.id=t.source_id;

CREATE OR REPLACE VIEW financial.approved_tuition_comparison AS
SELECT * FROM financial.fee_review_queue
WHERE review_status='approved' AND extraction_status='structured'
  AND billing_period <> 'unknown' AND effective_year IS NOT NULL
  AND degree_level NOT IN ('Mixed','Unknown','Graduate')
  AND is_estimate=false AND amount_max IS NULL;
