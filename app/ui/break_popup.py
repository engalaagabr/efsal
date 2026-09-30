"""Break popup dialog — the friendly reminder to move and stretch."""

import random

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib

from app.services.timer_service import TimerService
from app.utils.constants import BREAK_TIPS, DEFAULT_BREAK_COUNTDOWN
from app.utils.time_utils import format_duration


class BreakPopup(Adw.Window):
    """A calming break reminder popup window."""

    def __init__(self, application, active_minutes: int,
                 on_acknowledge=None, on_snooze=None):
        super().__init__(
            application=application,
            title="Time for a break",
            default_width=420, default_height=480,
            resizable=False, modal=True, deletable=True,
        )
        self._on_acknowledge = on_acknowledge
        self._on_snooze = on_snooze
        self._active_minutes = active_minutes
        self._timer = TimerService(DEFAULT_BREAK_COUNTDOWN)
        self._timer.on_tick = self._on_timer_tick
        self._timer.on_complete = self._on_timer_complete
        self._build_ui()
        self.set_hide_on_close(True)

    def _build_ui(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        header = Adw.HeaderBar()
        header.add_css_class("flat")
        header.set_show_end_title_buttons(True)
        header.set_title_widget(Gtk.Label())
        main_box.append(header)

        content = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=16,
            margin_start=32, margin_end=32, margin_top=8, margin_bottom=32,
            halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER, vexpand=True,
        )



        title = Gtk.Label(label="Time for a break")
        title.add_css_class("title-1")
        title.set_margin_top(4)
        content.append(title)

        subtitle = Gtk.Label(
            label=f"You've been active for {self._active_minutes} minutes"
        )
        subtitle.add_css_class("body")
        subtitle.add_css_class("dim-label")
        subtitle.set_wrap(True)
        subtitle.set_justify(Gtk.Justification.CENTER)
        content.append(subtitle)

        selected_tips = random.sample(BREAK_TIPS, min(5, len(BREAK_TIPS)))
        tips_label = Gtk.Label(label=" · ".join(selected_tips))
        tips_label.add_css_class("break-tips")
        tips_label.add_css_class("dim-label")
        tips_label.set_wrap(True)
        tips_label.set_justify(Gtk.Justification.CENTER)
        tips_label.set_max_width_chars(35)
        tips_label.set_margin_top(16)
        content.append(tips_label)

        self._countdown_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=4,
            halign=Gtk.Align.CENTER, margin_top=8,
        )
        self._countdown_box.set_visible(False)
        self._countdown_label = Gtk.Label(label="01:00")
        self._countdown_label.add_css_class("break-countdown")
        self._countdown_box.append(self._countdown_label)
        hint = Gtk.Label(label="Take a moment for yourself")
        hint.add_css_class("caption")
        hint.add_css_class("dim-label")
        self._countdown_box.append(hint)
        content.append(self._countdown_box)

        button_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=10,
            halign=Gtk.Align.CENTER, margin_top=20,
        )
        self._ack_btn = Gtk.Button(label="I'm up")
        self._ack_btn.add_css_class("pill")
        self._ack_btn.add_css_class("suggested-action")
        self._ack_btn.set_size_request(200, -1)
        self._ack_btn.connect("clicked", self._on_ack)
        button_box.append(self._ack_btn)

        snooze_btn = Gtk.Button(label="5 min later")
        snooze_btn.add_css_class("pill")
        snooze_btn.set_size_request(200, -1)
        snooze_btn.connect("clicked", self._on_snooze_clicked)
        button_box.append(snooze_btn)

        self._timer_btn = Gtk.Button(label="Start 1-min timer")
        self._timer_btn.add_css_class("pill")
        self._timer_btn.add_css_class("flat")
        self._timer_btn.set_size_request(200, -1)
        self._timer_btn.connect("clicked", self._on_start_timer)
        button_box.append(self._timer_btn)

        content.append(button_box)
        clamp = Adw.Clamp()
        clamp.set_maximum_size(420)
        clamp.set_child(content)
        clamp.set_vexpand(True)
        main_box.append(clamp)
        self.set_content(main_box)

    def _on_ack(self, button):
        self._timer.stop()
        if self._on_acknowledge:
            self._on_acknowledge()
        self.close()

    def _on_snooze_clicked(self, button):
        self._timer.stop()
        if self._on_snooze:
            self._on_snooze()
        self.close()

    def _on_start_timer(self, button):
        self._countdown_box.set_visible(True)
        self._timer_btn.set_visible(False)
        self._countdown_label.set_label(format_duration(DEFAULT_BREAK_COUNTDOWN))
        self._timer.start()

    def _on_timer_tick(self, remaining):
        GLib.idle_add(self._countdown_label.set_label, format_duration(remaining))

    def _on_timer_complete(self):
        GLib.idle_add(self._countdown_label.set_label, "Done!")
        GLib.idle_add(self._ack_btn.set_label, "Done")


class ManualBreakPopup(Adw.Window):
    """Simpler popup for manually triggered breaks."""

    def __init__(self, application, on_done=None):
        super().__init__(
            application=application, title="Take a moment",
            default_width=380, default_height=460,
            resizable=False, modal=True, deletable=True,
        )
        self._on_done = on_done
        self._timer = TimerService(DEFAULT_BREAK_COUNTDOWN)
        self._timer.on_tick = self._on_tick
        self._timer.on_complete = self._on_complete
        self._build_ui()
        self._timer.start()

    def _build_ui(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        header = Adw.HeaderBar()
        header.add_css_class("flat")
        header.set_show_end_title_buttons(True)
        header.set_title_widget(Gtk.Label())
        main_box.append(header)

        content = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=12,
            margin_start=32, margin_end=32, margin_top=8, margin_bottom=32,
            halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER, vexpand=True,
        )



        title = Gtk.Label(label="Take a moment")
        title.add_css_class("title-1")
        title.set_margin_top(4)
        content.append(title)

        tips_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=6,
            margin_top=20, halign=Gtk.Align.CENTER,
        )
        for tip in ["Stand up.", "Roll your shoulders.",
                     "Stretch your back.", "Drink some water.",
                     "Look away from the screen for a minute."]:
            lbl = Gtk.Label(label=tip)
            lbl.add_css_class("body")
            lbl.add_css_class("dim-label")
            tips_box.append(lbl)
        content.append(tips_box)

        self._countdown_label = Gtk.Label(
            label=format_duration(DEFAULT_BREAK_COUNTDOWN)
        )
        self._countdown_label.add_css_class("break-countdown")
        self._countdown_label.set_margin_top(20)
        content.append(self._countdown_label)

        done_btn = Gtk.Button(label="Done")
        done_btn.add_css_class("pill")
        done_btn.add_css_class("suggested-action")
        done_btn.set_size_request(180, -1)
        done_btn.set_halign(Gtk.Align.CENTER)
        done_btn.set_margin_top(16)
        done_btn.connect("clicked", self._on_done_clicked)
        content.append(done_btn)

        clamp = Adw.Clamp()
        clamp.set_maximum_size(400)
        clamp.set_child(content)
        clamp.set_vexpand(True)
        main_box.append(clamp)
        self.set_content(main_box)

    def _on_done_clicked(self, btn):
        self._timer.stop()
        if self._on_done:
            self._on_done()
        self.close()

    def _on_tick(self, remaining):
        GLib.idle_add(self._countdown_label.set_label, format_duration(remaining))

    def _on_complete(self):
        GLib.idle_add(self._countdown_label.set_label, "Done!")
