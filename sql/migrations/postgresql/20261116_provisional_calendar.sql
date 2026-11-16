-- Reference teaching blocks from MINEDU 2026; the user authorized provisional
-- dates on 16 November 2026. The first start follows the supplied school date.
-- Never replace dates already edited or confirmed by the teacher.
INSERT INTO academic_calendar(academic_year,period,date_from,date_to,confirmed)
VALUES
    (2026,1,'2026-03-20','2026-05-15',FALSE),
    (2026,2,'2026-05-25','2026-07-24',FALSE),
    (2026,3,'2026-08-10','2026-10-09',FALSE),
    (2026,4,'2026-10-19','2026-12-18',FALSE)
ON CONFLICT(academic_year,period) DO NOTHING;
