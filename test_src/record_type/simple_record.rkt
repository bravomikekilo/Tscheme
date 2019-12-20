(define-record Point
    [x Number]
    [y Number]
)

(define-record Rect
    [up-left Point]
    [down-right Point]
)

(define (rect-area rect)
    (let
        ([up-left (Rect.up-left rect)]
         [down-right (Rect.down-right rect)])
        (* (- (Point.y up-left) (Point.y down-right))
            (- (Point.x down-right) (Point.x up-left)))))

(define (rect-area-match rect)
        (match rect
               [(Rect [Point right-x up-y] [Point left-x down-y])
                (* (- up-y down-y)
                   (- left-x right-x))]))

(define test-rect (Rect (Point 2 3) (Point 4 1)))

(println (rect-area test-rect))
(println (rect-area-match test-rect))
