# jigsaw
All the tedium of a jigsaw puzzle, from the command line!

```
usage: jigsaw.py [-h] [--dim H W] [-i pieces] [--labels] [--coord] [--piece]
                 [--placed] [--pile] [--stats]

optional arguments:
  -h, --help  show this help message and exit
  --dim H W   width and height (default 5x5)
  -i pieces   The number of pieces to seed the board with (default 1)
  --labels    Show numeric labels along the puzzle axes

feedback modes:
  --coord     Display the grid each time a piece is tried in aspot
  --piece     Display the grid after failing to find a spot for a piece
  --placed    Display the grid after placing any piece
  --pile      (Default) Display the grid after trying all letters in the pile
  --stats     Solve the puzzle silently, showing only final stats
```

The main purpose of jigsaw.py is to answer this question: How long would it take me to solve an [impossible jigsaw puzzle](http://www.zazzle.com/impossible+puzzles) by brute-forcing it?

When you run jigsaw.py from the command line, this is what the algorithm does:

1. Creates a puzzle board, (Default 5x5, customize with `--dim H W`).
2. Places one piece on the board as a "seed" to build off of (customize the number with `-i pieces`)
3. Put all the pieces in a bag, shuffle them, then do this with each:
    1. Test it in each exposed location on the board (i.e. open locations next to at least one already-placed piece)
    2. Place it if the location is found
    3. Save it in the discard pile if the location isn't found
4. Shuffle the remaining pieces and try again until all pieces are placed.
5. Show you some stats about how many comparisons were needed.

`jigsaw` doesn't try to solve the edges first, which would probably speed up the solution quite a bit. With the current algorithm, the result is not encouraging for puzzlers: by around 300 pieces, the number of comparisons starts surpassing what's humanly realistic, and it goes up exponentially from there. Try it yourself!