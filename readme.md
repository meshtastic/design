# Meshtastic Styleguide

The meshtastic logo is derived from the appearance/aesthetics of physical LoRa modulation. 

![Idea](styleguide/idea.png)

Throughout an ongoing [community-driven design process on the meshtastic forum](https://meshtastic.discourse.group/t/design-guideline-logo/2022/41) it was refined and given additional meaning.

CycloMiles said:
> While inspired by the LoRa chirps, your logo resembles the shape of a tent [...] One could also think of mountainous areas…

This narrative also resonates with Lure.Exciting.Salads:
> I see the mountains (Where I plan on putting repeaters in my area, and where I plan on using these in general) and I also see tents (I plan on using these while backpacking, camping, snowshoeing, hunting, etc.) so it definitely speaks to me. I also clearly see the “M”
> When scaled down to under 10mm on my phone screen, I definitely feel like simple is better.

Besides the positive associations, some concerns were brought up by TitanTronics:
> I like the logo and the idea behind it, only if you notice the letter “M” seems to start out as an “i” and “a” making it look like “iaeshtastic” because you used the letter “a” and the letter “i” also in Meshtastic itself, suggesting that the two symbols used in the logo are an “i” and an “a” put together which makes “ia”

User ChomeBlue also brought up the ambiguity and non-obvious meaning:
> A non-nerd won’t relate to any of this. Not to mention; to the uninitiated, I don’t believe this would even be recognized as an "M’

Despite those concerns, most of the people involved could imagine the "LoRa-M" as the new logo. Ambiguity to a point is not detrimental if the form of the logo is able to communicate the right thing and people can identify themselves with it. Often, ambiguity makes it possible in the first place to create a distinct logo that will be associated with a brand/idea/community.


## Margins and spacing

![Margins](styleguide/margins.png)

## Sizes for different use cases

![Sizes](styleguide/sizes.png)

## The typeface 

![Typeface](styleguide/typeface.png)

## Colors

Primary/Foreground color:

`#2C2D3C`

`RGB 44 45 60`

Secondary/Background/Accent color:

`#67EA94`

`RGB 103 234 148`

![Colors](styleguide/colors.png)

## A note to developers

If you are a developer using these images inside a Meshtastic® application, you can run bin/generate-pngs.sh to regenerate PNGs from the vector files.  This script will be updated as needed to generate appropriate
'standard' sized/colored images for various platforms.

## Notes for android developers

#### App launcher icons

The icons should be generated with a separate SVG for foreground and background.  The dimensions of the svg should be 108 pixels square.  The middle logo should be 58 pixels wide and high.

If you need to regenerate android icons follow [this](https://developer.android.com/studio/write/image-asset-studio#create-adaptive) procedure.  It will also generate the play store icons.  You should name the icon ic_launcher2.

#### Action bar icons

To regenerate the action bar icons use the Image Asset tool to import logo/svg/Mesh_Logo_White.svg.  Use 0% padding, HOLO_DARK theme and name the generated asset "app_icon".