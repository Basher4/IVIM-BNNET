from fixedpoint import FixedPoint
import numpy as np

from perf_model.config import OVERFLOW

bs_init = [
    [ 0xc897c962189e6ef0421bebc5079d3b26, 0x7758a587380b3847af0355d1be8ae220, 0x516054eb0079d3941e891b72ad00e4c8 ],    [ 0x51b100f82f9eeae5f37bb9c731857f40, 0xf8bf7cdb59c982bb5f6561f8f03287e1, 0xbdc0ee60d7c1061c7a38bff54825514d ],
    [ 0xb1abaa285f55156e8037c44d5ef896d8, 0x9a08ffa49463ddfb6ccad19c6a8f4c43, 0x3ab83a40ea169370489e932e16fca06f ],    [ 0xb25dab2eae46dfe1d05c34981b7690e1, 0xbe907ff98a0499d9bc76c8ebe6578644, 0x9a329c0c0f2b4c1219933e961392d5a2 ],
    [ 0x54bc8d50604ca77e638a095e36471b06, 0x4570adc2d7d4fc07a17d601a929afd72, 0x860b22a2501a57fac8f62a91e68a81cc ],    [ 0x7f79f373689ba1ae71d26e5a4b7c49dc, 0x93d0f1bd34451d106e84ae4cc9f2b4d8, 0xbabf18ad295fb268617375963dadca84 ],
    [ 0x6bdbc58757dc9df8a74e3703f163ca90, 0x1ae167603fd205a591672e602cb51954, 0x22e229dfcadaf785a4dbfd08804ee737 ],    [ 0xec6831e8652ca8fd818a30bf5d8d79fb, 0xee3223ce88cc84a5d99ebc73f0c0e145, 0x3385a9d31d35a2973b912b8285c7b78b ],
    [ 0xb35ab1a5a0278abc98e1831572901e4a, 0xd7ca606c53fa434ecc2c7df3362afcb3, 0x84e28b8e018feafcab2d2178e260dcb6 ],    [ 0xe017993981295afb4b74a6bcba08329f, 0x296886601ab5168cff9656b175baf085, 0xa4ad3084e023583066bec3ec53063d33 ],
    [ 0x98aa722234afcc2ad8c06ffe0a20847c, 0xeac8f84e59f006542ef14c53cf660603, 0xcf079fcfb217c073b6e5bead03167e5c ],    [ 0x4435ca6e893ff02832c7ccba2c5b614b, 0x310af0af12f9b9e2e69589567d6ae1fb, 0xf7100e816a01639f88b9cd18eebe1845 ],
    [ 0x1ec5104376e2d3280d00e3601529ab39, 0x6d4afbc598d54b91be62a769858204d8, 0xd3e1dd5d3651b999f870ce1f3b1c4d5b ],    [ 0xe014e2ecbd8f40f813523c6e41d037bc, 0x3fd17926623677ea9f2df183b7166443, 0x1f015e6598c9b793b05abdfdca10dbe5 ],
    [ 0x0c8b70ea30e55bf693054033e88f829d, 0x7b65ac539c3a64f517d3e41de6e617a3, 0xd524742d11c8d79ff249ca7239f8e8a3 ],    [ 0xac5a5f67ee4e3c0f132dd7841039e8bc, 0xfd373be1442bbb63ce1b54604d1e20ba, 0xde8c0e943ad6c40d87afc797702fe5b3 ],
    [ 0x8d85b44ba20ee0c5c5f88301b89af34c, 0xfd9144d8141b7b278e5971888bb02a52, 0x163c40a6262c1aa24fbe32e281970a84 ],    [ 0xb915b42d957c58e2055dbb9be714043a, 0x686caa804a3414f6b5392e6d9ad434e6, 0xaa77b8a9ea1d84d5bf25a787399783ad ],
    [ 0x79a65a15e9981f6a3a732a03d063446d, 0xd1f543a5dca514a2a5ab317d32d90ff0, 0x4ccc1d095e55c4fe2e4f1edb2afd68eb ],    [ 0x3adc9b180191e89595969f4608574899, 0xed22f859123d1a28df267ff7671c1042, 0xf6a25efa0ecc6dbf4c7bc4c4c121326d ],
    [ 0xc516f6e5d4dc3eaeb60e7d94c73ccfe3, 0x5c5ed0d024299e59444e8e8ed2a50084, 0xc63b986ee3161f50ff18f12a7bb9fb71 ],    [ 0x7e2ff7842731dabc81af71d396ed5774, 0xbc534f823ab414bcaa3a398e3c55e34e, 0x90f533b2fc9915f0ec6c293f2f390f63 ],
    [ 0x359a3cd4849ade45f00e0e5898089cc8, 0xe8d3873ea81f2b69ed2c04edd17ee0d6, 0x47f97710312426e1ea631d7815cb2d41 ],    [ 0x1c4fa0cfc1e900b4ace11b0ac0da84dd, 0xc1c434ab0677a3f22496f181be2a33e5, 0x2feb7d5834f7eb2dc91a44be33aee0fd ],
    [ 0x3636970480dbb072132f6c860dddd7e0, 0xfe81847423f8aa5a0ab63f0715b9caf8, 0xf172b67b9c0d5a12b58e319cefd69269 ],    [ 0x4ca65af98231cef513bd2076466f0fc6, 0xb93372503ef99a1ac59a194f3e6457c6, 0x1ef6cdb272f256573655798c10b7f071 ],
    [ 0xed2da1c745df535437feffa0b6e1686b, 0x2afb60fe0a4f8202793e80a1bbfccabd, 0xd2234acb388aa9702076e4257314f98a ],    [ 0x726bac377fb1f46e37d64a984fc5fcf3, 0xa992b7e02d43e500370a370af885c35f, 0x71f36c71855c706b51f9fce27b1170bf ],
    [ 0x88410a21a02bbf31840ead8f1e93a037, 0xd7ec5c5803672dc15daf1e5a6f9c9c29, 0xbf097c4a011d24e2f0d1b969762bfc28 ],    [ 0xe05227e9e08982dcf6fd3f583ee580a6, 0x4f0fe6d249500db45ac77c7b0252cd37, 0x0dd597f2051bb39c310c8b6ab6ee8317 ],
    [ 0xce1d053b34b4f6b184b4b9af27663b78, 0x97573641b203fbf80c9fcb55de88b9bb, 0xedd4b49b7c67abd90069a751f5cf3c18 ],    [ 0x30c3b8db62ecd10945da899b4c44ed34, 0xb3ce40b1dcd859bd5246c3345aad77ae, 0xa8e1c7c74b77230753a6dbe70d107ba8 ],
    [ 0x3000e6f47433d6b7716a1fdcdaa6c631, 0x9ea496852536de80323a906d8ec28a8d, 0xbf9fe56238f04c95ebb5893917dee26b ],    [ 0x7ea26c04343ed1fb107ba69daa1d3d58, 0xacfee387e6274bd81492fc90c9863812, 0x37e952268e972f405c79958c741a9ba8 ],
    [ 0xe94b64f53e756ce0240793b2911ff06f, 0x85ce1631c9cae9be1431a6bf30eaad89, 0x6c81bcc77b60724163636294b50112f3 ],    [ 0x6fe8d1846ffcfd53250e291df1f29037, 0x6689db2d67d66befd6b70a66b85b8c3b, 0x157c8bce9a4270d30d714dfe8780c37e ],
    [ 0xe8cb3db9ca5c2abc0c0a65f95614f278, 0xe440198ef72cb043bc54ca4f55663c6c, 0xd6d0111c472c7ca1639a5f7e325b1ff5 ],    [ 0x9868292a55ff27bc380988799c9855b5, 0xa5dc63efc843600dd032d03eb0cc57de, 0x9e32d4be6e3c4c68a88dc50bf186f9ca ],
    [ 0x3391426ce3702318b9ed8ef1c7da78d3, 0x4d17d3c77c4752d9f830a4e99ca174da, 0x7ded2fb33b6d7bfb541e9e4036a531ee ],    [ 0x7f68bb4cb28aa440b6773ffa3203790e, 0xb5487af127fbfb7356136f863f73a65b, 0xe48fbe4fc115d1b13f25318eaae85c7c ],
    [ 0x653ae17fec88c25de014d38ef62a22b7, 0xba97d04044f0f14dacaca80a634699df, 0x24688a095e4d987914b7671046eeb210 ],    [ 0xa37e4f7dacb2da77d3981ddd8536acc3, 0xa16d6f2a9acf2496c32f17aaf07e8e81, 0x60147dc7bc813150a7d6f79599c94a16 ],
    [ 0x3e22737b8cda1e3c84aaa0e6a1da88fc, 0xd7b60304429e19b5cd47d93851494bfc, 0x0a7ab52a30e09cf066d605c064af62ac ],    [ 0xf116105c265229514010347e886eb07d, 0xa0b598d7b96a59c907a1681779405502, 0xdd193ba8c19db9d7e93c859f763bb1c2 ],
    [ 0x93deb1aef0b57052db7a97653a37e866, 0x433d151ee226d62b3ed8a2f017646112, 0x261a023c6b572d0bd896a08811c62ff4 ],    [ 0xe3d204d504ee726d79407b86df38de4e, 0x8b459149dc641e8fd894e4565d13b0c6, 0xf2f928216297b3ac4c7322920dcb0e41 ],
    [ 0xe4d8c723f10a7d1361b5b262f82db254, 0x3cf03edd7b4d3ec3b03730a28e5d7d39, 0xf8226ee114fbbfc4bf42d16722828a81 ],    [ 0xfbcae33b2b1e7c230986daa73d2f4d19, 0xe1d66200d2f02a18a2e3fc35336d2d1a, 0xb723ec9f1d51fcd31086cf87c64bf214 ],
    [ 0xdb1fe4c685d45bd532e208f1c07e4584, 0x05fe172a90a145782101ec3ff3c2ddfd, 0x33e5278e50b87395667c95120ddb378e ],    [ 0x9869e8b57091ca94dfbce2f1f74ecd9e, 0xd82d0039d0c7cf5d00377bf05de432df, 0xfdba5d894e3e1ec83c035b4efdbe54a6 ],
    [ 0x5cd3ff4c7d6c11489766fe80be8f3f06, 0xe8a76cf1215ce379d8462edf86343a0e, 0xd3bca2793ca10eafafab0d8e6df29944 ],    [ 0xf892a8a89b77b9736ca53e70215928bc, 0x3da786a7a52f09d067d7dec10f0b4efa, 0x95cf176e87cd23853a3caadd2c0af4cd ],
    [ 0x8211089244943ec7c76e7e6dbafb5b27, 0x80242d73de95555931090070f1b29a60, 0xbbe3ab580c033bfa8298a1cc2f312f68 ],    [ 0x564a46eeec0e077c0e4ad32348a36c59, 0x96b1f10d72832c4386e751f5aec27d96, 0x31b18003439c939f6c0ad4137ddd06a8 ],
    [ 0x3aa5b0d134adcf555c78772fe6610b4d, 0xbc35b9a64a86b4f4fc2bdb1e21ce705c, 0xa551a3e43519b669e9eafe0c6d7e4601 ],    [ 0xe05c934d58d2a401b39d584d1c9aef9f, 0xad977a0817a2eec986c3832dc45b68fe, 0xec178583bca5c848c1631a187f41611f ],
    [ 0xe87dfb6346e627557cc1366171acf875, 0xa178b773f418991f160e6784bdbf15cd, 0x930bfa9237d212c3fabf6bfa90369593 ],    [ 0x6fa7bde9364248c4bcb1fe016fdfc191, 0x317de9d73b7b978d7ec92612ed729015, 0x8caa729ceed2a3df042286781dbce548 ],
    [ 0x7480254cd1f1c83a5d32a9a60b14918a, 0x9d1331e835a10b7fdda2feda4327fed6, 0x429cff0a162a091bf1e9b567a2ef3c3a ],    [ 0x9dd43e18fb74c87815ca89033cd33839, 0x4dc385ca3e5319f6ce9e741a50c6093b, 0x5c1cebc9eb3e93c14ad946e0b9b2aefe ],
    [ 0xa12c050ae0d1aad919906654b96d2665, 0x039e451a2e1737982c58781dd525fd19, 0x0f063877feb9fd9ed917f4ff6284f9cc ],    [ 0x3fe756a2b020cfb47ac19574516c682f, 0x3443711bfa8c6029b1d988a415d0a29e, 0x9d6d0b8f096343cc79d20d8aecd33d29 ],
    [ 0x313279002884a675effc02aa8edccf33, 0x3e05ad4f513f52cebe0f0abc0de60d59, 0xd851745f7dfcf96c0491432d89ae2243 ],    [ 0x555c5c9282f941c09202974c27bcbe41, 0x5d7d7253dade5f4832431f4b85149754, 0x2618e7175d22eeb7e8fead86c7ccfaab ],
    [ 0x528ef1f465f004ba52d216cd1baa15b0, 0x10b227218e2ba9c198f12a2be01a910b, 0xa28678ee7e2b76c58ef7bf09635f46bf ],    [ 0x7cac783edc7d788479fdf1c4777ca3d7, 0x3c9d6144a399cf6d353516a0680e7a31, 0xc400de23f6380645b4a8a3fba2b0e9c8 ],
    [ 0xf78a6468fbffbd8910bfb7a21234a73d, 0x33196f5f6005b171dbd004b862a0a04d, 0x14331b743faa073c753d6dae8db6f714 ],    [ 0x924638ffbd8266070324af8b53437c9a, 0x360e81a7dc72cc59a5e88cc930fc5613, 0xa6c2d21e33166e76d84292347acb5308 ],
    [ 0x01fa76242c35baec2b6619e80cc2e5dc, 0xc5405d6cfed13d8f48431e69783be374, 0x01a7b9b30fd2f335954816e2b7e4c5fc ],    [ 0x4ee56e34ee4cd9e5c0f5b6ee6c42c40c, 0xf28d3d391c1523d3120a22e8ebbdbd2a, 0xf556223243c5367b0ca337f418d4af87 ],
    [ 0xc4b2fd0484e646a60beda76be5717f7e, 0xf71dcc5976d5734ad2b17cfe64ef20bb, 0x008f93202b0ca17c82f6ae1187a9dfa2 ],    [ 0xbbdd3c64415f2a3011e420effa86e35a, 0xfb770ffb31d2fc900e883565b666cd10, 0xc4763fe1db6928dd77274476e9deb792 ],
    [ 0xe74644227c1717364e99ce88f9d00dbf, 0x307c56dc034f7a11f51e0d7e27362952, 0x09bad79c9b8db784ad5485859e594c29 ],    [ 0x990151860294710143f95fc5f8f13d5c, 0xd3c2bbed89b68ff9421d7f0c75d5888b, 0xda2a2d4eb2423dbdefc3edb8fcf23576 ],
    [ 0x697daf1bb7d1a1fa44cc946fe71cf6af, 0x2b6438cf8e2ef74506ebe71f5e8a23d3, 0xbb0df4f612eac50a50e5076642cf7721 ],    [ 0xa76bb6d1ca6a5a1ba89e59c50beeab3b, 0x21da449808ce3566a87127491e1e4a06, 0x9c8a1a5461019f206b810dbcdda10925 ],
    [ 0x90196d3966ad4de0c0fbd09a3b2a43a8, 0x2296e9a486686e6fc2e119ba597ffe73, 0x5ed255177d955ee37f5f1977fc7d579b ],    [ 0xc4c7060b48c83ad48d23df20ab82420b, 0x88c487f477fde819ebc5184872936287, 0x75a92c4ea6c73ee03a09f52d3a51fbbf ],
    [ 0x585369608cd8e3a8a3403cbd1f2c3451, 0xc06f37386dd22a3eb0d786d7a6c75a9e, 0xd7979bc253543a9f8ace740fad0f025d ],    [ 0x76431a3c68f220faf2fd8380e0cc520c, 0x7b08c1f7236f56b4208fb605387eacef, 0xa29d5a409773e3614b427840dc46035b ],
    [ 0x3b569f7def5dd755e4e9d247e7c739eb, 0x04b98d283998426c26d84972d956060c, 0x50ccceb57a8fbab301914b61afbc0c1d ],    [ 0xcc9f7f8c67746d729846bd935cb9fe61, 0x623afcb638197b95fb1d1ef6236d545a, 0x1632db3b46b0ad3861d5b34250f83eec ],
    [ 0x31ac75db8602fe8d8730523bf36bb51c, 0x3c6bd159146d3b30aa66ffc4c13635e2, 0x20891bbd1bb2323001fb3353f1b0cec7 ],    [ 0x1c57c7c37ab449e28b3cb28e8f87264d, 0x7e35a2437edce47b0cdaaeb0c6a1cad8, 0x7b6c9bf92c4864e8e1fc6361e1a31707 ],
    [ 0xf82d0dc427b18614ac341c001fe6780c, 0x1b93dbc949758a486d4797f4a3c3f698, 0x07efc66d4ef8e4ccd5dae2dc9fedfbee ],    [ 0x296fda5728d5bd70b95753ca4c77ed91, 0xfc0dce52fe161c13cab5b3b10b771302, 0x98d564981b5593fdd8f55dda3518b7bb ],
    [ 0xc2bdb5367976a5cf49749803fbb62ca1, 0x3a8b3c4897b41d477cda8c4aa6cb582f, 0x549845996b6812d825ba42843c7101f9 ],    [ 0xc7c2da47792c08d59a5673d5f555b1ee, 0x7b71f4232a6d1c8e3da70a45cf17c917, 0x8c3bc82efa0557a905f668fee7f7523c ],
    [ 0xa6af3a418504882fe355c9774bd026a1, 0x1491073654c3c03e43063b9791060172, 0xeb9ea711225daece3f2957093b888952 ],    [ 0x91661f2e260a86a6e14143fb0e4a2609, 0x5371f66da25c1e5ccfba6ed8716aba40, 0xf76be4569115c034d9bae233a237bd5a ],
    [ 0xe14bab9e4342c483c67774fde6a31d06, 0xccccc07a550ca2ff68c5fa88feb09934, 0x57502c0a73d3712874df3f3150af1e13 ],    [ 0x78806ae28c7b4ec335af30ae223fe414, 0x77bc4a623b5a5627954c90cfd3547b91, 0xe495f0f1709d1c141f4c668f723a3b10 ],
    [ 0x80bf50f4a43e8678e7735862708da045, 0xebeadb168fecb0e90e084232b86a1097, 0x4aa969bb47828ebf0ddac560c52adf5f ],    [ 0xeef36e96c35ecdd65454fd3ad4d6d8db, 0x52d068287c73c700286042a6d4f87823, 0x3933898d8bb446820b30ca6cc51b59bd ],
    [ 0xb0c51ab56bc58dbcd0dbed33daa17972, 0xf3d89ee3f7ef2893fa46600eb12227e4, 0x3669f29eb8eadf55799a0961a70452b2 ],    [ 0x4fb293cc65bff776de6bff029a07f634, 0x5eb6f2185fd102800a819ba52c2df65f, 0x2f45e28fb9df033f3b5c743c379c0431 ],
    [ 0x6dd5a86c31c5394d30418f4e94765670, 0xcc2c993c07c2246ad7cebc3c145a5d6f, 0xf799c4d8c6cb880b1a19a72f0ebf9fc2 ],    [ 0x13e57d05e98569679bba01b42dd1b19b, 0x1708908a7d6e35090e0116a7d711c125, 0x4ba58967870e8e3862ab0ea4f197b4ca ],
    [ 0x5664aefe4f54582d91a5bdb9fbc7743d, 0x3952117a13e0e80016a4f4c7133c461c, 0xa34fdada0b3c1ac471289419ba298186 ],    [ 0x47e42a40eee18d26648cac90c04a7927, 0x2b44b5c0dea74922dd5f12e74b27886d, 0xcb742ace2b194d903e58a8270e27532b ],
    [ 0xc723857e58a7bfcffce57d32fb50e486, 0x425581ae446f2b9cf72d708c8508c2c7, 0xc598f2ef91e8c84b53a998442dc39c57 ],    [ 0x86d9ecaa1e935b5c0c6dc3bbd9397f94, 0x19b59cf0775dfd7dc0bd4ed31ea53c85, 0x52765722c023b882d64a77d4f680154a ],
    [ 0x2ac3ab7f57be490b47619566fc55c8fe, 0xc701f61b959d604fcd4650693f70317c, 0xc2799e67b2a0fd84b8619922ed6ab79a ],    [ 0xb14ed0b582e524110e3ad48e7c93776e, 0x830e2c5bc186c717ec47daac139d7f3f, 0xe8c484b18da0b26bd3ac1390ddbfa3a1 ],
    [ 0xfce5e70d1290e6291421d041efce45d6, 0x2fee715aebe0e434be0f6c5a27bce192, 0xcbaa073f70d16fe6422ec46dfa9a1ac8 ],    [ 0x8aaebac6e452021bc869a32e31cbdc88, 0xfa1d869c43a7fffa4bec94bc063baec6, 0xa08a3d9c221940a4edf0ecb62721f40a ],
    [ 0xb907c460fe6e768378dfcbefb5230422, 0xb20489b79f07d5e72aa430e5611acf77, 0x0ef2dec34161d3297e970f4be3e72a3e ],    [ 0xb3d8f1c20a64b4a775948465c04c36be, 0x20b8c0f0357d274ef31e1849474e72e6, 0x75b0e58c8e12fe67925b0d81b1f27ffc ],
    [ 0x41c0bd2212a84aa06ae948ae8b6933f4, 0xebf3af32e1e3a0c4f14f2f989bcfd11e, 0x07b4528e61f7c683686e67ca5b385602 ],    [ 0x8c6155a8d791241b5fbfc7f26a727b11, 0xc9d8e8ea060cc0a3c22c66be8f7f8a13, 0xe2d7f4d55a6a2b24398789c3785cbaaa ],
    [ 0xa3f0aa820be458c9b3532d61161b2514, 0x9d480c211a53bb51e928a7c1d25f169c, 0x10b1d35e6d100e9f58726ecb8dd1f310 ],    [ 0xbe0227ac0cb7cda2957d63ff8adf2486, 0xb69af84c4bfa3dd0a7c3597825ec3d8d, 0x636947cb1c74abe9b1b873fb187735d7 ],
    [ 0xc0a0c8564088c4155b2f72ba79a21d4a, 0x62e77beb5704043a1acb6ecec447c68b, 0x66d490c25de8c74e7ce7ab7d786725b9 ],    [ 0x604f46c93a3fb621b20040605da4fef0, 0xcbcb285f26feb1c9589a36ff8677a8ba, 0xcefe071a6a8679d946f0cc81a4b2c2aa ],
    [ 0xcd454b2b651d6d7cbdfd7dc1eb72eac7, 0x70f6aa4985cc92603854fc510a2d7a30, 0x4a45681096830b46b3c32d32b940e8eb ],    [ 0xad7b2614304672e0c36ea4a8361c817f, 0xdd527bf1199c87cc217bfa26531c4bb8, 0x701251cbb4755e61c46f9cdab1d087aa ],
    [ 0x0e99fa8aaf4731f70fc8e430885f12d0, 0x7481c297abb149498da7e24e7eb0488c, 0x0ad0682899d8066b0faa3c71afa8130e ],    [ 0x94148df01205264c9d5b329ef356ac0a, 0x697445a00f8af373bcef51717a2df3d3, 0x7edd9fd00ced0d099540b3ee58cb61ce ],
    [ 0x9664da75145a28238ed382109bf46c60, 0x341c2e7d5921ee9795e32fa7317c5239, 0xed3b4df307f6067cecc7e8a693c387f1 ],    [ 0x3dadfbfe238a988196235b7fe76e32bb, 0xb76acef6b502ab571a65c10a94a527be, 0x8197f1cd5fb615185cdf9f047f672821 ],
    [ 0x3d81d3286e4abeea08d10198770abc41, 0xdd617a2f0295116ca8d1666ca773c20e, 0x6fcd2e10f4da0aa85bcebe12b28272e9 ],    [ 0x9d7ac24812c882ec2ac3d7d5b4acdbf4, 0x367d3a15418b78eff5a7916bfa963366, 0x9b3a4427d11af95b77c17c207b325977 ],
    [ 0xc4fc96d162d0797c76ec0b292c5a4f88, 0x2b9b572fa4d6ad6837c75fa0f3ecfe73, 0x19fe5a2a6fdb879270c6b292dcf8b7ca ],    [ 0x9e7bb4a953a6f66b83ccb9a215037bbb, 0xa780b65e6d2a5230da807b909ab1fc4e, 0x76a915f224d5e98562f623610bfbf8aa ],
    [ 0x5a878577e7c1da9ad4d479a3ba51ab2e, 0xa8759da60760668acf4d8914320cda0d, 0xbe39039683db411d127a01432d71fe57 ],    [ 0x6c9ad6a581f2ebb049cc37e017c55740, 0x654bd8be9e473f9131ad6c25de5c960a, 0xe9d998d13c513197055c063548d891e9 ],
    [ 0x85e750c095487eb57067f04992d025a8, 0x843c85b0166d0e4e160895867c1127be, 0xf1e3ed43027cd5e729798e971c10d05a ],    [ 0x682f600123d1ced8169be5219d627828, 0x1619f3d020f73d5588e5661d12a9c1bb, 0xff577a9bf0a39f5733fbe254322ab365 ]
]

class LFSR:
    def __init__(self, seed):
        self.shr = FixedPoint(seed, signed=False, m=128, n=0, overflow=OVERFLOW)

    def tick(self):
        out = self.shr.bits[127]
        next = self.shr.bits[120] ^ self.shr.bits[125] ^ self.shr.bits[126] ^ self.shr.bits[127]
        self.shr = self.shr << 1 | next

        return out
        

class BernoulliSampler:
    def __init__(self, out_width):
        self.lfsrs = [[LFSR(bs_init[i][j]) for j in range(3)] for i in range(out_width)]

    def get_mask(self):
        elem = ""
        for ls in self.lfsrs:
            elem = str(ls[0].tick() ^ ls[1].tick() ^ ls[2].tick()) + elem
        return FixedPoint(f"0b{elem}", False, m=128, n=0, overflow=OVERFLOW)
