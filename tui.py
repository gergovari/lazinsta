import editor
import uuid
from post_publisher import Post

from PIL import Image

class QuitNotice(Exception):
	pass
class RerunNotice(Exception):
	pass

class TUI:
	def __init__(self, 
		prefix, 
		txt_gen, 
		img_gen, 
		img_editor, 
		preset_manager,
		post_publisher
	):
		self._prefix = prefix
		self._txt_gen = txt_gen
		self._img_gen = img_gen
		self._img_editor = img_editor
		self._preset_manager = preset_manager
		self._post_publisher = post_publisher

	def start(self):
		while True:
			try:
				print("Type '0' to choose a preset.")
				print("Type '1' to generate posts.")
				print("Type 'q' to exit.")
				choice = self._get_choice(1)
				if choice == 0:
					preset = self._choose_preset()
					self._preset_manager.set(preset)
				elif choice == 1:
					try:
						while True:
							try:
								inp = input("The number of posts in this group (empty means one): ")
								if not inp:
									count = 1
								else:
									count = int(inp)
								break
							except ValueError:
								print("Invalid count!")
						posts = []
						for i in range(1, count + 1):
							posts.append(self._create_post(i))
						for post in posts:
							self._post_publisher.publish(post)
					except QuitNotice:
						print("Returning to main menu.")
				else:
					print("Unknown command!")
			except KeyboardInterrupt:
				break
			except QuitNotice:
				break
			except RerunNotice:
				pass
		print("Goodbye!")
	def _create_post(self, count = 1):
		text = self._choose_text() if self._ask_binary("Do you want to generate text?") else editor.edit(contents="".encode("UTF-8")).decode("UTF-8")
		tags = self._choose_tags(text) if self._ask_binary("Do you want to generate tags?") else []
		image = self._choose_image(text) if self._ask_binary("Do you want to generate images?") else Image.open("default_img.jpg")
		final = self._edit_image(image, text, count)						
		return Post(
			image = final, 
			caption = text, 
			tags = tags
		)
	def _print_texts(self, texts):
		print()
		print("-" * 20)
		for i, text in enumerate(texts):
			print(f"{i+1}: {text}")
		print("-" * 20)
		print()
	def _ask_binary(self, text):
		while True:
			inp = input(f"{text} ('y' or 'n'): ")
			if inp == "y" or inp == "n":
				return inp == "y"
			else:
				continue
	def _get_choice(self, length):
		while True:
			try:
				inp = input(f"{self._prefix} ")
				if inp[0] == "q":
					raise QuitNotice
				elif inp[0] == "r":
					raise RerunNotice
				elif int(inp) <= length:
					return int(inp)
				else:
					print("Out of range choice!")
			except QuitNotice:
				raise QuitNotice
			except RerunNotice:
				raise RerunNotice
			except:
				print("Unknown error!")

	def _edit_image(self, image, text, count = 1):
		cropped = self._img_editor.crop_center(image)
		blurred = self._img_editor.blur(cropped)
		faded = self._img_editor.fade(blurred)
		written = self._img_editor.write_text(faded, text)
		if count > 1:
			written = self._img_editor.write_count(written, count - 1)
		branded = self._img_editor.write_brand(written)
		return branded
	def _choose_image(self, text):
		run_gen = True
		while run_gen:
			print("Generating images...")
			images = self._img_gen.generate(text)
			for i, image in enumerate(images):
				image.save(f"{i+1}.jpg")
				print(f"Saving image {i+1}.jpg...")
			print("Type your choice to use an image.")
			print("Type 'r' to rerun generation.")
			print("Type 'q' to return to the last screen.")
			while True:
				try:
					return images[self._get_choice(len(images)) - 1]
				except QuitNotice:
					run_gen = False
					break
				except RerunNotice:
					break
		raise QuitNotice
	def _choose_text(self):
		topic = input("Make the prompt more specific (if the preset allows): ")
		run_gen = True
		while run_gen:
			print("Generating texts...")
			texts = self._txt_gen.generate(
				self._preset_manager.get("instruction").replace(
					"{topic}", 
					topic
				)
			)
			while True:
				self._print_texts(texts)
				print("Choose the used text.")
				print("Type 'r' to rerun generation.")
				print("Type 'q' to return to the last screen.")
				try:	
					choice = self._get_choice(len(texts))
					text = texts[choice - 1]
					return editor.edit(contents=text.encode("UTF-8")).decode("UTF-8")
				except QuitNotice:
					run_gen = False
					break
				except RerunNotice:
					break
	def _choose_preset(self):
		presets = self._preset_manager.get_presets()
		self._print_texts(presets)
		print("Choose the your new preset.")
		while True:
			try:
				return presets[self._get_choice(len(presets)) - 1]
			except QuitNotice:
				raise QuitNotice
			except RerunNotice:
				continue
	def _choose_tags(self, text):
		run_gen = True
		while run_gen:
			print("Generating tags...")
			batches = list(
				map(
					lambda batch: batch.split(" "), 
					self._txt_gen.generate(
						self._preset_manager.get("instruction_tags").replace(
							"{text}", text
						)
					)
				)
			)
			self._print_texts(batches)
			print("Type your choice to use a tag batch.")
			print("Type 'r' to rerun generation.")
			print("Type 'q' to return to the last screen.")
			while True:
				try:
					return batches[self._get_choice(len(batches)) - 1]
				except QuitNotice:
					run_gen = False
					break
				except RerunNotice:
					break
		raise QuitNotice
