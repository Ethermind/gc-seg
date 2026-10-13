-- =============================================================================
-- Giaconi-Capra® PAS — Seed Data
-- NOTE: do NOT include the id column in the INSERTs. Ids are assigned by the
-- PostgreSQL SERIAL/IDENTITY sequence; inserting explicit ids leaves the
-- sequence out of sync and subsequent app INSERTs fail with
-- "duplicate key value violates unique constraint".
-- =============================================================================

INSERT INTO reviews (name, role, avatar, rating, text, is_approved, created_at)
VALUES
    (
        'Carlos Mendoza',
        'Cliente Asegurado - Auto y Hogar',
        'CM',
        5,
        'Excelente atención de Leandro y Paola. Cuando tuve un siniestro con el vehículo gestionaron todo de inmediato sin vueltas. Es fundamental tener un asesor que te responda cuando realmente lo necesitás.',
        TRUE,
        NOW()
    ),
    (
        'Sofia Giannini',
        'Socia Directora - Comercio Pyme',
        'SG',
        5,
        'Revisaron los seguros que teníamos en nuestra empresa y nos bajaron los costos mejorando la cobertura de ART y Flotas. Transparencia total desde la primera reunión.',
        TRUE,
        NOW()
    ),
    (
        'Martín Rodríguez',
        'Inquilino - Caución para Alquiler',
        'MR',
        5,
        'Necesitaba una garantía de alquiler urgente y Paola me guió paso a paso para gestionarla en 24 horas. Súper profesional y con la mejor predisposición.',
        TRUE,
        NOW()
    )
ON CONFLICT DO NOTHING
RETURNING *;

INSERT INTO coverages (categoria, titulo, icono, descripcion, badge, orden, activo, created_at)
VALUES
    -- Personas (product content, kept in Spanish)
    ('personas', 'Auto', 'car', 'Protegé tu vehículo frente a accidentes, robo, incendio y daños, con distintas alternativas de cobertura para elegir la que mejor se adapte a vos.', NULL, 1, TRUE, NOW()),
    ('personas', 'Moto', 'motorbike', 'Coberturas para que disfrutes tu moto con mayor tranquilidad, protegiéndote frente a responsabilidad civil, robo, incendio y otros imprevistos.', NULL, 2, TRUE, NOW()),
    ('personas', 'Hogar', 'home', 'Protegé tu casa y todo lo que hay en ella frente a incendio, robo, daños y otros imprevistos que pueden afectar tu patrimonio.', NULL, 3, TRUE, NOW()),
    ('personas', 'Vida', 'heart-pulse', 'Una forma de cuidar económicamente a quienes más querés. Brinda respaldo ante situaciones inesperadas y ayuda a proteger la estabilidad de tu familia.', NULL, 4, TRUE, NOW()),
    ('personas', 'Retiro', 'trending-up', 'Empezá hoy a construir el capital que querés disfrutar mañana. Un plan de ahorro a largo plazo pensado para complementar tus ingresos futuros.', NULL, 5, TRUE, NOW()),
    ('personas', 'Accidentes Personales', 'activity', 'Protegete vos o protegé a quienes realizan trabajos para vos frente a las consecuencias de un accidente.', NULL, 6, TRUE, NOW()),
    ('personas', 'Viajes', 'plane', 'Viajá con respaldo ante imprevistos lejos de casa, con asistencia frente a emergencias médicas y otras situaciones.', NULL, 7, TRUE, NOW()),
    ('personas', 'Bicicletas y Ecomovilidad', 'bike', 'Protegé tu bicicleta, monopatín eléctrico y otros medios de movilidad personal frente a robo e imprevistos, incluyendo Responsabilidad Civil.', NULL, 8, TRUE, NOW()),
    ('personas', 'Celulares y Portátiles', 'smartphone', 'Protegé los dispositivos que te acompañan todos los días, como celulares, notebooks y tablets, frente a robo y otros imprevistos.', NULL, 9, TRUE, NOW()),
    ('personas', 'Caución para Alquileres', 'key-round', 'El seguro de caución puede reemplazar la garantía propietaria y brindar al propietario el respaldo necesario.', NULL, 10, TRUE, NOW()),

    -- Empresas (product content, kept in Spanish)
    ('empresas', 'Comercio', 'store', 'Protegé tu negocio, mercadería, instalaciones y equipamiento frente a los principales imprevistos.', NULL, 1, TRUE, NOW()),
    ('empresas', 'Consorcio', 'building', 'Protegé el edificio, sus espacios comunes y la responsabilidad del consorcio frente a los principales riesgos e imprevistos.', NULL, 2, TRUE, NOW()),
    ('empresas', 'Responsabilidad Civil', 'scale', 'Protegé tu patrimonio frente a reclamos por daños que, como consecuencia de tu actividad, puedas ocasionar a terceros.', NULL, 3, TRUE, NOW()),
    ('empresas', 'ART', 'hard-hat', 'Protección para tus empleados frente a accidentes de trabajo y enfermedades profesionales, cumpliendo con la normativa vigente.', 'Nuevo', 4, TRUE, NOW()),
    ('empresas', 'Caución Empresas', 'file-text', 'Una alternativa para garantizar el cumplimiento de distintas obligaciones sin inmovilizar capital.', NULL, 5, TRUE, NOW()),
    ('empresas', 'Transporte', 'truck', 'Protegé las mercaderías durante su traslado frente a pérdidas o daños que puedan ocurrir en el camino.', NULL, 6, TRUE, NOW()),
    ('empresas', 'Equipos y Maquinarias', 'wrench', 'Protegé las herramientas, maquinarias y equipos esenciales para desarrollar tu actividad frente a distintos daños.', NULL, 7, TRUE, NOW()),
    ('empresas', 'Flotas', 'car-front', 'Protegé todos los vehículos de tu empresa bajo una cobertura pensada para simplificar su administración.', NULL, 8, TRUE, NOW()),
    ('empresas', 'Retiro para Empleados', 'award', 'Ofrecé a tus colaboradores un beneficio pensado para su futuro, ayudándolos a construir un ahorro para complementar su jubilación.', 'Nuevo', 9, TRUE, NOW())
RETURNING *;

INSERT INTO faqs (pregunta, respuesta, categoria, orden, activo, created_at)
VALUES
    (
        '¿Por qué contratar mi seguro a través de un Productor Asesor de Seguros?',
        'Porque no solo te ayudamos a contratar una póliza. Analizamos distintas alternativas, te explicamos qué estás cubriendo y te acompañamos durante la vigencia del seguro y, especialmente, cuando ocurre un siniestro.',
        'general',
        1,
        TRUE,
        NOW()
    ),
    (
        '¿Trabajan con una sola compañía de seguros?',
        'No. Trabajamos con distintas compañías aseguradoras, lo que nos permite evaluar alternativas y buscar la cobertura que mejor se adapte a tus necesidades.',
        'general',
        2,
        TRUE,
        NOW()
    ),
    (
        '¿Tiene algún costo adicional contratar el seguro con ustedes?',
        'No. Nuestro asesoramiento como Productores Asesores de Seguros no representa un costo adicional para vos sobre el precio de la póliza.',
        'general',
        3,
        TRUE,
        NOW()
    ),
    (
        '¿Puedo pedir una cotización sin compromiso?',
        'Sí. Contanos qué necesitás asegurar y analizamos las alternativas disponibles para ofrecerte una propuesta acorde a tus necesidades.',
        'cotizacion',
        4,
        TRUE,
        NOW()
    ),
    (
        '¿Qué tengo que hacer si tengo un siniestro?',
        'Contactanos lo antes posible. Te vamos a indicar qué documentación necesitás, cómo realizar la denuncia y te acompañaremos durante la gestión del siniestro ante la compañía.',
        'siniestros',
        5,
        TRUE,
        NOW()
    ),
    (
        '¿Puedo cambiar de compañía si ya tengo un seguro contratado?',
        'Sí. Podemos revisar tu cobertura actual y evaluar otras alternativas. Antes de realizar cualquier cambio, verificamos fechas, condiciones y coberturas para evitar que quedes sin protección.',
        'general',
        6,
        TRUE,
        NOW()
    ),
    (
        '¿Puedo contratar un seguro completamente online?',
        'En muchos casos, sí. Podemos realizar la cotización, solicitar la documentación y gestionar la emisión de manera digital, manteniendo siempre el asesoramiento personalizado.',
        'cotizacion',
        7,
        TRUE,
        NOW()
    ),
    (
        '¿Qué información necesito para pedir una cotización?',
        'Depende del seguro que necesites. Con algunos datos básicos podemos comenzar y después te indicaremos específicamente qué documentación necesitamos para avanzar.',
        'cotizacion',
        8,
        TRUE,
        NOW()
    ),
    (
        '¿También trabajan con empresas y comercios?',
        'Sí. Asesoramos a comercios, profesionales, consorcios y empresas, desde coberturas específicas hasta programas integrales que contemplen distintos riesgos de la actividad.',
        'empresas',
        9,
        TRUE,
        NOW()
    ),
    (
        '¿Cómo sé si las coberturas que tengo actualmente son suficientes?',
        'Podemos revisar tus pólizas actuales, analizar sumas aseguradas, coberturas y necesidades reales, y ayudarte a detectar posibles faltantes o coberturas que convenga actualizar.',
        'general',
        10,
        TRUE,
        NOW()
    ),
    (
        '¿Después de contratar, con quién me comunico si necesito algo?',
        'Con nosotros. Queremos que tengas siempre a quién recurrir. Desde una modificación en tu póliza hasta un siniestro o una consulta sobre tu cobertura, nuestro trabajo es acompañarte también después de la contratación.',
        'general',
        11,
        TRUE,
        NOW()
    )
RETURNING *;

-- =============================================================================
-- Defensive sequence resync (idempotent).
-- Guarantees the next generated id is greater than the existing max(id),
-- even if rows were inserted again with explicit ids.
-- =============================================================================
SELECT setval('reviews_id_seq', COALESCE((SELECT MAX(id) FROM reviews), 1), (SELECT MAX(id) FROM reviews) IS NOT NULL);
SELECT setval('coverages_id_seq', COALESCE((SELECT MAX(id) FROM coverages), 1), (SELECT MAX(id) FROM coverages) IS NOT NULL);
SELECT setval('faqs_id_seq', COALESCE((SELECT MAX(id) FROM faqs), 1), (SELECT MAX(id) FROM faqs) IS NOT NULL);
