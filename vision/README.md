# Vision Health walkthrough reel

1920 × 1080, 60 fps, about 81 s. One iPhone walks through the app in the order of the prototype screen recording, with a chapter caption beside it. Twice the phones spread out side by side, in the style of the Claude Design cut.

Every screen is rebuilt as real UI (text, buttons, bars, the color wheel), so it stays sharp at full HD. Only the drawn artwork is cut from your captures: the activity icons, the smartwatch, the doctor portraits and the Eye Health Education illustrations. Nothing moves unless it has a reason to: the phone glides only between chapters, and every motion settles with the same soft ease.

| Time | What happens |
| --- | --- |
| 0 – 4.7 s | The phone rises in on the splash dot. The dot sends out two rings, then becomes the app icon on **Welcome to Vision Health**. Tap **Get Started** |
| 5 – 10.7 s | **Connect your devices**: the orbits flow while it searches, the Noise ColorFit Ultra 3 card slides up, **CONNECT** turns into **✓ CONNECTED**, then **Cool, let’s move forward** |
| 11 – 26 s | **Getting to know you**: the intro, Question 1, the vision number typed in (-0.5 and -0.75, 2 years), then Questions 2 to 5. Each answer is added to the list at the top. The medical history form comes last |
| 26 – 29 s | **Summary**: the tab bar slides up and the three progress bars fill |
| 29 – 38.5 s | **Analysis**: the activity bars grow, **iPhone is Too Close** turns into **Screen Distance ✓**, then it scrolls to the Time in Daylight chart |
| 38.5 – 42 s | **Sharing**, then back to **Summary**. Tap **MORE** on Eye Exercises |
| 43 – 47 s | Eye Exercises, Eye Tests, Eye Games and Eye Health Education side by side |
| 47 – 63 s | Eye Games comes forward. **Color Match**: swipe to the instructions, **Start Training**, the "hue" countdown, two rounds of turning the ball to the colour, then the results |
| 63 – 71 s | **Your experience**: four questions, then "schedule a virtual consultation?" **Yes** |
| 71 – 74 s | **Virtual Consultation**: the doctor cards come in |
| 74 – 81 s | Analysis, Sharing and Virtual Consultation side by side, then the Vision Health end card |

```sh
python3 vision/extract.py                    # after changing anything in source/ → assets/*.png + assets/embedded.js
node vision/render.mjs                       # → exports/vision-health-walkthrough.mp4
node vision/render.mjs --stills 12 30.5 50   # PNG stills to check a moment
node vision/render.mjs --from 40 --to 60     # render just part of it
```

Open `index.html` in Chrome to play and scrub it. All timings are in the TIMELINE section of its script. Each chapter starts from a time variable (`T_MORPH`, `T_FOUND`, `T_SPREAD`, `T_CM` …), so you can retime a chapter by changing one number. The captions are in `caps`.

The font is Inter, which is close to SF Pro. If Inter isn't installed, the page falls back to the system font, which is SF Pro on a Mac.
