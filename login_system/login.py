from utils import *
import string


USERNAME_INPUT = TextInput(Text('Username: ', pos(WIDTH/4, HEIGHT/2), WIDTH/2, HEIGHT/8, font=MediumFont), active=True, _input={'text_color': Colors.WHITE}, placeholder={'text': 'Enter your username', 'text_color': (50,) * 3}, accepted_chars=string.ascii_letters + string.digits + '_', min_length=1, max_length=20)
PASSWORD_INPUT = TextInput(Text('Password: ', pos(WIDTH/4, 5*HEIGHT/8), WIDTH/2, HEIGHT/8, font=MediumFont), _prev=USERNAME_INPUT, password=True, max_length=40, placeholder=USERNAME_INPUT.placeholder.format('Enter your password'), min_length=1)

LEFT_BUTTON = Button(Text('YES', pos(WIDTH/4, 5*HEIGHT/8), WIDTH/5, HEIGHT/10, background_color=Colors.GREEN, font=MediumFont), {'background_color': Colors.BRIGHT_GREEN})
RIGHT_BUTTON = Button(Text('NO', pos(3*WIDTH/4, 5*HEIGHT/8), WIDTH/5, HEIGHT/10, background_color=Colors.RED, font=MediumFont), {'background_color': Colors.BRIGHT_RED})


def verify_register(create: bool | User = False) -> None:
    skip = isinstance(create, User)

    if not skip:
        details = []
        for text_input in USERNAME_INPUT.group:
            if not text_input.verify():
                return
            details.append(''.join(text_input.input.text))

        user = User(username=details[0].lower(), password=details[1])
    else:
        user = create
    player = get_user(session := mem['session'], user)
    if not player:
        if not create:
            scene = mem['game'].scene
            return setattr(scene, 'scene', scene.wait_for_confirmation)
        session.add(user)
        session.commit()

        set_scene(mem['game_scene'])
        mem['user'] = user
    else:
        if not skip and not player.verify_password(user.password):
            return PASSWORD_INPUT.show_error('Incorrect password')
        set_scene(mem['game_scene'])
        mem['user'] = player


LOGIN = Button(Text('Login', pos(WIDTH * 3 / 8, HEIGHT * 3 / 4), background_color=Colors.BLUE, text_color=(255, 165, 0), font=MediumFont), {'background_color': Colors.BRIGHT_BLUE, 'text_color': (255, 205, 45)}, verify_register)
GUEST_BUTTON = LOGIN.modify({'text': 'Guest Mode', 'position': pos(WIDTH * 5 / 8, HEIGHT * 3 / 4)}, action=partial(verify_register, User(username='guest', password='')))


class LoginScene(BaseScreen):
    def draw_login(self) -> None:
        Text('Login / Register a new account', pos(WIDTH/2, HEIGHT/4), font=Font(70)).draw()
        USERNAME_INPUT.draw(self)
        PASSWORD_INPUT.draw(self)
        LOGIN.draw(self)
        GUEST_BUTTON.draw(self)

    def wait_for_confirmation(self) -> None:
        Text(f'No user named {"".join(USERNAME_INPUT.input.text)} found, create a new account?', pos(WIDTH/2, 3*HEIGHT/8), font=MediumFont).draw()
        LEFT_BUTTON.action = partial(verify_register, True)
        RIGHT_BUTTON.action = partial(setattr, self, 'scene', self.draw_login)
        LEFT_BUTTON.draw(self)
        RIGHT_BUTTON.draw(self)

    scene = draw_login


if True:
    from scenes import set_scene
