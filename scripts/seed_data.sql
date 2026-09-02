-- =============================================================================
-- Giaconi-Capra® PAS — Seed Data for Testimonials
-- =============================================================================

INSERT INTO reviews (name, role, avatar, rating, text, is_approved)
VALUES
    (
        'Carlos Mendoza',
        'Cliente Asegurado - Auto y Hogar',
        'CM',
        5,
        'Excelente atención de Leandro y Paola. Cuando tuve un siniestro con el vehículo gestionaron todo de inmediato sin vueltas. Es fundamental tener un asesor que te responda cuando realmente lo necesitás.',
        TRUE
    ),
    (
        'Sofia Giannini',
        'Socia Directora - Comercio Pyme',
        'SG',
        5,
        'Revisaron los seguros que teníamos en nuestra empresa y nos bajaron los costos mejorando la cobertura de ART y Flotas. Transparencia total desde la primera reunión.',
        TRUE
    ),
    (
        'Martín Rodríguez',
        'Inquilino - Caución para Alquiler',
        'MR',
        5,
        'Necesitaba una garantía de alquiler urgente y Paola me guió paso a paso para gestionarla en 24 horas. Súper profesional y con la mejor predisposición.',
        TRUE
    )
ON CONFLICT DO NOTHING;
