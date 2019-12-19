(define-sum Shape
    [Rect Number Number]
    [Circle Number])

(define (area s) (match s
    [(Shape.Rect length width) (* length width)]
    [(Shape.Circle radius) (* radius radius)]
))

(define rect (Shape.Rect 10 10))

(print (area rect))
