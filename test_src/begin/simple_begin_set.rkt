(define x 2)

(define (simple-begin-set) (begin
    (set! x 1)
    x
))

(begin
    (simple-begin-set)
    (print x))