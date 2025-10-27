from bot.core.driver import MyDriver
from bot.ui.helpers import exp_selectors_dict, e2_selectors_dict, heroes_selectors_dict


async def bot_interface():
    driver = await MyDriver().get_driver()

    await driver.evaluate("() => window.selectedExp = null;")
    await driver.evaluate("() => window.selectedE2 = null;")
    await driver.evaluate("() => window.selectedHeroes = null;")
    await driver.evaluate("() => window.questEnabled = false;")
    script = f"""
        var botIcon = document.createElement('div');
        botIcon.id = 'botIcon';
        botIcon.innerText = 'N8Bot';
        document.body.appendChild(botIcon);
        botIcon.style = `
            position: fixed;
            width: 45px;
            height: 45px;
            background: linear-gradient(145deg, #1a1a1a, #000000);
            color: #00ff88;
            border-radius: 50%;
            bottom: 94.5vh;
            left: 16vw;
            display: flex;
            cursor: pointer;
            z-index: 999;
            justify-content: center;
            align-items: center;
            font-family: 'Arial Black', sans-serif;
            box-shadow: 0 4px 15px rgba(0, 255, 136, 0.3);
            border: 2px solid #00ff88;
            transition: all 0.3s ease;
        `;


        let mainBox = document.createElement('div');
        mainBox.id = 'mainBox';
        document.body.appendChild(mainBox);

        mainBox.style = `
            position: fixed;
            bottom: 50vh;
            left: 2vw;
            width: 250px;
            height: 375px;
            background: #001a00;
            border: 2px solid #00ff88;
            overflow: hidden;
            z-index: 999;
            display: none;
            flex-direction: column;
            gap: 5px;
            padding: 10px;
            align-items: center;
            justify-content: center;
            border-radius: 20px;
            box-shadow: 0 0 20px rgba(0, 255, 136, 0.2);
            transform: perspective(1000px) rotateX(5deg);
        `;

        let btnClose = document.createElement('div');
        btnClose.id = 'btnClose';
        mainBox.appendChild(btnClose);

        btnClose.style = `
            position: absolute;
            z-index: 99;
            top: 10px;
            right: 10px;
            width: 30px;
            height: 30px;
            cursor: pointer;
            background: #002200;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 1px solid #00ff88;
        `;
        
        let closeIcon = document.createElement('div');
        closeIcon.id = 'closeIcon';
        closeIcon.innerText = 'x';
        btnClose.appendChild(closeIcon);

        closeIcon.style = `
            color: #00ff88;
            font-size: 24px;
            margin-bottom: 3px;
        `;

        var customWindow = document.createElement('div');
        customWindow.id = 'custom-window';
        mainBox.appendChild(customWindow);

        customWindow.style = `
            position: relative;
            display: flex;
            gap: 8px;
            width: 90%;
            background: #000d00;
            border: 1px solid #00ff88;
            border-radius: 15px;
            padding: 15px;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        `;

        var header = document.createElement('h1');
        header.innerText = 'Wybierz expowisko';
        header.style = `
            color: #00ff88;
            margin: 0;
            font-size: 1.2em;
            text-shadow: 0 0 5px rgba(0, 255, 136, 0.5);
        `;
        customWindow.appendChild(header);

        var selectElement = document.createElement('select');
        selectElement.style = `
            width: 70%;
            padding: 6px;
            border-radius: 8px;
            background: #002200;
            color: #00ff88;
            border: 1px solid #00ff88;
            cursor: pointer;
            font-family: Arial, sans-serif;
        `;
        selectElement.name = 'expOptions';
        selectElement.id = 'expOptions';

        var optionsMap = {exp_selectors_dict};
        for (var key in optionsMap) {{
            if (optionsMap.hasOwnProperty(key)) {{
                var option = document.createElement('option');
                option.value = key;
                option.text = optionsMap[key];
                selectElement.appendChild(option);
            }}
        }}

        customWindow.appendChild(selectElement);

        var selectButton = document.createElement('button');
        selectButton.style = `
            background: #002200;
            color: #00ff88;
            border: 1px solid #00ff88;
            padding: 4px 30px;
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            font-weight: bold;
        `;
        selectButton.innerText = 'Select';
        selectButton.onclick = function() {{
            var selectedOption = selectElement.options[selectElement.selectedIndex].text
            window.selectedExp = selectedOption;
        }};
        customWindow.appendChild(selectButton);

        botIcon.onclick = function() {{
            mainBox.style.display = 'flex';
        }};

        btnClose.onclick = function() {{
            mainBox.style.display = 'none';
        }}
        
        closeIcon.onclick = function() {{
            mainBox.style.display = 'none';
        }}

        var header2 = document.createElement('h1');
        header2.innerText = 'Wybierz elite2';
        header2.style = `
            color: #00ff88;
            margin: 0;
            font-size: 1.2em;
            text-shadow: 0 0 5px rgba(0, 255, 136, 0.5);
        `;
        customWindow.appendChild(header2);

        var selectElement2 = document.createElement('select');
        selectElement2.style = `
            width: 70%;
            padding: 6px;
            border-radius: 8px;
            background: #002200;
            color: #00ff88;
            border: 1px solid #00ff88;
            cursor: pointer;
            font-family: Arial, sans-serif;
        `;
        selectElement2.name = 'e2Options';
        selectElement2.id = 'e2Options';

        var optionsElity2 = {e2_selectors_dict};
        for (var key in optionsElity2) {{
            if (optionsElity2.hasOwnProperty(key)) {{
                var option2 = document.createElement('option');
                option2.value = key;
                option2.text = optionsElity2[key];
                selectElement2.appendChild(option2);
            }}
        }}

        customWindow.appendChild(selectElement2);

        var selectButton2 = document.createElement('button');
        selectButton2.style = `
            background: #002200;
            color: #00ff88;
            border: 1px solid #00ff88;
            padding: 4px 30px;
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            font-weight: bold;
        `;
        selectButton2.innerText = 'Select';
        selectButton2.onclick = function() {{
            var selectedOption2 = selectElement2.options[selectElement2.selectedIndex].text
            window.selectedE2 = selectedOption2;
        }};
        customWindow.appendChild(selectButton2);


        var header3 = document.createElement('h1');
        header3.innerText = 'Wybierz herosa';
        header3.style = `
            color: #00ff88;
            margin: 0;
            font-size: 1.2em;
            text-shadow: 0 0 5px rgba(0, 255, 136, 0.5);
        `;
        customWindow.appendChild(header3);

        var selectElement3 = document.createElement('select');
        selectElement3.style = `
            width: 70%;
            padding: 6px;
            border-radius: 8px;
            background: #002200;
            color: #00ff88;
            border: 1px solid #00ff88;
            cursor: pointer;
            font-family: Arial, sans-serif;
        `;
        selectElement3.name = 'heroesOptions';
        selectElement3.id = 'heroesOptions';

        var optionsHeroes = {heroes_selectors_dict};
        for (var key in optionsHeroes) {{
            if (optionsHeroes.hasOwnProperty(key)) {{
                var option3 = document.createElement('option');
                option3.value = key;
                option3.text = optionsHeroes[key];
                selectElement3.appendChild(option3);
            }}
        }}

        customWindow.appendChild(selectElement3);

        var selectButton3 = document.createElement('button');
        selectButton3.style = `
            background: #002200;
            color: #00ff88;
            border: 1px solid #00ff88;
            padding: 4px 30px;
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            font-weight: bold;
        `;
        selectButton3.innerText = 'Select';
        selectButton3.onclick = function() {{
            var selectedOption3 = selectElement3.options[selectElement3.selectedIndex].text
            window.selectedHeroes = selectedOption3;
        }};
        customWindow.appendChild(selectButton3);

        var header4 = document.createElement('h1');
        header4.innerText = 'Questy';
        header4.style = `
            color: #00ff88;
            margin: 0;
            font-size: 1.2em;
            text-shadow: 0 0 5px rgba(0, 255, 136, 0.5);
        `;
        customWindow.appendChild(header4);

        var questToggleContainer = document.createElement('div');
        questToggleContainer.style = `
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 5px;
            margin-top: 2px;
        `;

        var questToggleLabel = document.createElement('span');
        questToggleLabel.innerText = 'Włączone:';
        questToggleLabel.style = `
            color: #00ff88;
            font-weight: bold;
        `;

        var questToggle = document.createElement('input');
        questToggle.type = 'checkbox';
        questToggle.id = 'questToggle';
        questToggle.style = `
            width: 40px;
            height: 20px;
            accent-color: #00ff88;
            cursor: pointer;
        `;
        questToggle.onchange = function() {{
            window.questEnabled = questToggle.checked;
        }};

        questToggleContainer.appendChild(questToggleLabel);
        questToggleContainer.appendChild(questToggle);
        customWindow.appendChild(questToggleContainer);
        


        // --- Drag & Drop ---
        let dragTarget = mainBox;
        let offsetX = 0, offsetY = 0;
        let isDragging = false;

        dragTarget.addEventListener('mousedown', (e) => {{
            if (e.button !== 0) return;
            const interactiveTags = ['SELECT', 'OPTION', 'BUTTON', 'INPUT', 'LABEL'];
            if (interactiveTags.includes(e.target.tagName)) return;

            isDragging = true;
            offsetX = e.clientX - dragTarget.getBoundingClientRect().left;
            offsetY = e.clientY - dragTarget.getBoundingClientRect().top;
            dragTarget.style.transition = 'none';
        }});

        document.addEventListener('mousemove', (e) => {{
            if (!isDragging) return;
            dragTarget.style.left = `${{e.clientX - offsetX}}px`;
            dragTarget.style.top = `${{e.clientY - offsetY}}px`;
        }});

        document.addEventListener('mouseup', () => {{
            if (!isDragging) return;
            isDragging = false;
            dragTarget.style.transition = 'all 0.3s ease';
        }});
        """
    await driver.evaluate(script)


async def make_postrefresh_action():
    driver = await MyDriver().get_driver()
    script = """
        window.onbeforeunload = () => sessionStorage.removeItem('refreshed');
        let reloaded = 0;
        if (window.performance.getEntriesByType && !sessionStorage.getItem('refreshed')) {
            const nav = window.performance.getEntriesByType("navigation")[0];
            if (nav && nav.type === "reload") {
                sessionStorage.setItem('refreshed', 'true');
                reloaded = 1;
            }
        }
        return reloaded;
    """
    result = await driver.evaluate(script)
    if result == 1:
        await bot_interface()


async def get_selected_exp():
    driver = await MyDriver().get_driver()
    return await driver.evaluate("() => window.selectedExp")


async def get_selected_elita2():
    driver = await MyDriver().get_driver()
    return await driver.evaluate("() => window.selectedE2")


async def get_selected_heroes():
    driver = await MyDriver().get_driver()
    return await driver.evaluate("() => window.selectedHeroes")


async def get_quest_enabled():
    driver = await MyDriver().get_driver()
    return await driver.evaluate("() => window.questEnabled")


async def set_selected_exp_to_default():
    driver = await MyDriver().get_driver()
    await driver.evaluate(
        f"""
        window.selectedExp = 'Wybierz';
        let selectElement2 = document.getElementById('expOptions');
        let options2 = selectElement2.options;
        for (let i = 0; i < options2.length; i++) {{
            if (options2[i].text === window.selectedExp) {{
                selectElement2.selectedIndex = i;
                break;
            }}
        }}
    """
    )


async def set_selected_exp_to_new_value(value):
    driver = await MyDriver().get_driver()
    await driver.evaluate(
        f"""
        window.selectedExp = "{value}";
        let selectElement2 = document.getElementById('expOptions');
        let options2 = selectElement2.options;
        for (let i = 0; i < options2.length; i++) {{
            if (options2[i].text === window.selectedExp) {{
                selectElement2.selectedIndex = i;
                break;
            }}
        }}
    """
    )
